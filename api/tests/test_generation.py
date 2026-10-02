from collections.abc import Iterator
from datetime import date
from threading import Event
from time import monotonic, sleep
from typing import cast

import httpx
import pytest
from fastapi.testclient import TestClient
from inspection_fixture import InspectionSource

from app.api.generation import get_generation
from app.domain import (
    POLICY,
    DemandCell,
    InvalidSelection,
    MonthlyDemand,
    PlanningMonth,
    ScheduleContext,
    SchedulingDataset,
    ShiftType,
    StaffLevel,
    Wish,
    WishEntry,
    WishType,
)
from app.main import app
from app.settings import Settings
from app.solver.generation import Generation, GenerationBusy, GenerationJob, GenerationRequest, JobState
from app.solver.model.objectives import OBJECTIVES
from app.solver.models import RunConfiguration, Solution, SolutionStatus
from app.solver.review import Review
from app.solver.service import SolverService

JANUARY = PlanningMonth(year=2026, month=1)
REQUEST = GenerationRequest(planning_unit_ids=(101,), planning_month=JANUARY, timeout_seconds=30)
EARLY = 1113
CONFIGURATION = RunConfiguration(
    policy=POLICY,
    timeout_seconds=30,
    search_workers=None,
    random_seed=None,
)
INFEASIBLE = Solution(status=SolutionStatus.INFEASIBLE, configuration=CONFIGURATION, wall_time_seconds=0)


def save_demand(source: InspectionSource, station_id: int = 101) -> None:
    cells = tuple(
        DemandCell(
            date=JANUARY.start.replace(day=day), shift_id=EARLY, staff_level=StaffLevel.PROFESSIONAL, required_count=1
        )
        for day in (5, 6)
    )
    source.service.save_demand(MonthlyDemand(planning_unit_id=station_id, planning_month=JANUARY, cells=cells))


def finished(generation: Generation) -> GenerationJob:
    deadline = monotonic() + 30
    while (job := generation.latest()) is None or job.state == JobState.RUNNING:
        assert monotonic() < deadline, "generation did not finish"
        sleep(0.01)
    return job


class HeldSolve:
    """A solve that runs until released, so tests can observe a running job."""

    def __init__(self, result: Solution | Exception = INFEASIBLE) -> None:
        self.started = Event()
        self.release = Event()
        self.result = result

    def __call__(self, dataset: SchedulingDataset, timeout: float) -> Solution:
        self.started.set()
        assert self.release.wait(5)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def read_nothing(**_: object) -> SchedulingDataset:
    return SchedulingDataset(
        planning_month=JANUARY,
        planning_units=(),
        shifts=(),
        demand_requirements=(),
        employees=(),
        planning_unit_memberships=(),
        availability=(),
        wishes=(),
        monthly_work_accounts=(),
        context=ScheduleContext(covered_from=JANUARY.start, covered_until=JANUARY.end),
    )


def test_generation_accepts_at_once_rejects_overlap_and_releases_after_finishing() -> None:
    solve = HeldSolve()
    generation = Generation(read_input=read_nothing, solve=solve, on_solved=Review().generated)

    job = generation.start(REQUEST)
    assert solve.started.wait(5)
    assert job.state == JobState.RUNNING
    assert generation.latest() == job
    with pytest.raises(GenerationBusy):
        generation.start(REQUEST)

    solve.release.set()
    done = finished(generation)
    assert (done.job_id, done.state) == (job.job_id, JobState.COMPLETED)
    # A completed job reports the solver status as found; infeasible is not a failure of the job.
    assert done.solution == INFEASIBLE
    assert done.finished_at

    solve.release.clear()
    assert generation.start(REQUEST).job_id != job.job_id
    solve.release.set()
    finished(generation)


def test_failed_solve_and_failed_input_release_the_lock() -> None:
    solve = HeldSolve(RuntimeError("solver crashed with internal details"))
    solve.release.set()
    generation = Generation(read_input=read_nothing, solve=solve, on_solved=Review().generated)

    generation.start(REQUEST)
    failed = finished(generation)
    assert failed.state == JobState.FAILED
    assert failed.solution is None
    assert failed.error
    assert "internal details" not in failed.error

    def invalid(**_: object) -> SchedulingDataset:
        raise InvalidSelection("not plannable")

    rejecting = Generation(read_input=invalid, solve=solve, on_solved=Review().generated)
    with pytest.raises(InvalidSelection):
        rejecting.start(REQUEST)
    assert rejecting.latest() is None
    rejecting = Generation(read_input=read_nothing, solve=solve, on_solved=Review().generated)
    assert rejecting.start(REQUEST).state == JobState.RUNNING
    finished(rejecting)


def test_generation_input_carries_the_month_wishes_of_station_and_jumper_pool_employees() -> None:
    source = InspectionSource()
    save_demand(source)
    early = WishEntry(type=WishType.PREFERRED_SHIFT, shift_id=EARLY)
    source.service.set_wish(employee_id=1, day=date(2026, 1, 12), entry=early)
    source.service.set_wish(employee_id=2, day=date(2026, 1, 13), entry=WishEntry(type=WishType.FREE_DAY))
    source.service.set_wish(employee_id=2, day=date(2026, 2, 2), entry=WishEntry(type=WishType.FREE_DAY))

    dataset = source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY)

    # Employee 1 belongs to the jumper pool; February's wish is outside the month.
    assert dataset.wishes == (
        Wish(employee_id=1, date=date(2026, 1, 12), **early.model_dump()),
        Wish(employee_id=2, date=date(2026, 1, 13), type=WishType.FREE_DAY),
    )


def test_generation_input_reads_absences_and_only_trusted_context_duties() -> None:
    source = InspectionSource()
    with pytest.raises(ValueError, match="No saved staffing demand"):
        source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY)
    save_demand(source)
    source.queries.clear()

    dataset = source.service.read_generation_input(planning_unit_ids=(101, 101), planning_month=JANUARY)

    # Polluted worked shifts (another plan, earlier output in the target plan) never become input:
    # the absence read selects no worked shift, and worked duties come only from trusted context plans.
    roster_queries = [sql for sql in source.queries if "TPlanPersonalKommtGeht" in sql]
    assert all("pkg.RefgAbw IS NOT NULL OR pkg.RefDienstAbw IS NOT NULL" in sql for sql in roster_queries[:-2])
    worked = [sql for sql in roster_queries if "pkg.RefDienste AS shift_id" in sql]
    assert len(worked) == 1
    assert "p.RefStati = :context_status_id" in worked[0]
    # The context plans span the five days before January that the rules reach; employee 2 worked
    # the night of December 31.
    assert (dataset.context.covered_from, dataset.context.covered_until) == (date(2025, 12, 27), JANUARY.end)
    [night] = dataset.context.duties
    assert (night.employee_id, night.date, night.shift_id, night.staff_level) == (
        2,
        date(2025, 12, 31),
        1690,
        StaffLevel.PROFESSIONAL,
    )
    # February 1 lies after the month: its approved absence reaches the last night of January.
    assert [(row.employee_id, row.date) for row in dataset.context.availability] == [(1, date(2026, 2, 1))]
    # The approved absence still binds planning.
    assert [(row.employee_id, row.date.day, row.reason) for row in dataset.availability] == [(1, 1, "U")]
    # Station 101 is assignable, jumper pool 201 is origin context; station 102 stays out of this run.
    assert [unit.planning_unit_id for unit in dataset.planning_units] == [101, 201]
    assert {row.planning_unit_id for row in dataset.planning_unit_memberships} == {101, 201}
    assert {row.planning_unit_id for row in dataset.demand_requirements} == {101}
    assert len(dataset.demand_requirements) == 2
    assert len(dataset.monthly_work_accounts) == 3


def test_generation_input_rejects_drifted_context_and_reports_missing_coverage() -> None:
    source = InspectionSource()
    save_demand(source)
    source.drifted_context_duty = True
    with pytest.raises(ValueError, match="does not match a reference shift"):
        source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY)

    source.drifted_context_duty = False
    source.context_plans = False
    context = source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY).context
    # Without trusted plans nothing around the month is known; the schedule check reports that gap.
    assert (context.covered_from, context.covered_until, context.duties) == (JANUARY.start, JANUARY.end, ())


def test_generation_input_times_the_reference_shifts() -> None:
    source = InspectionSource()
    save_demand(source)
    shifts = source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY).shifts

    assert [(s.code, s.type, s.start_minute, s.end_minute, s.net_work_minutes) for s in shifts] == [
        ("F", ShiftType.EARLY, 355, 805, 420),
        # A segment without paid minutes counts its full length.
        ("Z", ShiftType.INTERMEDIATE, 510, 855, 345),
        ("S", ShiftType.LATE, 795, 1260, 435),
        # The night ends at 06:10 on the next date.
        ("N", ShiftType.NIGHT, 1210, 1810, 555),
    ]
    # The gaps between segments are the unpaid breaks.
    night = shifts[-1]
    assert [(s.start_minute, s.end_minute) for s in night.segments] == [(1210, 1305), (1320, 1440), (1470, 1810)]

    source.missing_shift_times = True
    with pytest.raises(ValueError, match="Missing TimeOffice shift times"):
        source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY)


@pytest.fixture
def source() -> InspectionSource:
    return InspectionSource()


@pytest.fixture
def generation(source: InspectionSource) -> Iterator[Generation]:
    solver = SolverService(Settings(solver_num_search_workers=1))
    # Requests carry the minimum time limit; the HTTP contract needs a result, not a full-length search.
    generation = Generation(
        read_input=source.service.read_generation_input,
        solve=lambda dataset, timeout: solver.solve(dataset, timeout=min(timeout, 2)),
        on_solved=Review().generated,
    )
    yield generation
    generation.shutdown()


@pytest.fixture
def client(generation: Generation) -> Iterator[httpx.Client]:
    app.dependency_overrides[get_generation] = lambda: generation
    try:
        yield cast(httpx.Client, TestClient(app))
    finally:
        app.dependency_overrides.clear()


BODY = {"planning_unit_ids": [101], "planning_month": {"year": 2026, "month": 1}, "timeout_seconds": 30}


def test_http_generation_solves_the_saved_month(
    client: httpx.Client, source: InspectionSource, generation: Generation
) -> None:
    assert client.get("/generation").status_code == 404
    save_demand(source)

    started = client.post("/generation", json=BODY)
    assert started.status_code == 202
    assert started.json()["state"] == "running"
    finished(generation)
    job = client.get("/generation").json()

    assert job["job_id"] == started.json()["job_id"]
    assert job["state"] == "completed"
    assert job["request"]["planning_unit_ids"] == [101]
    solution = job["solution"]
    assert solution["status"] in {"optimal", "feasible"}
    # A found schedule always carries the independent check, apart from the solver status.
    assert solution["check"]["status"] == "accepted"
    assert [stage["name"] for stage in solution["stages"]] == [tier.name for tier in OBJECTIVES]
    assert solution["configuration"]["policy"]["balance_tolerance_minutes"] == 460
    for assignment in solution["assignments"]:
        assert assignment["planning_unit_id"] == 101
        assert assignment["staff_level"] in {"professional", "mfa"}


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ({**BODY, "timeout_seconds": 29}, 422),
        ({**BODY, "planning_unit_ids": []}, 422),
        ({**BODY, "planning_unit_ids": [201]}, 422),
        (BODY, 409),
    ],
)
def test_http_generation_rejects_invalid_or_incomplete_input(
    client: httpx.Client, body: dict[str, object], status: int
) -> None:
    response = client.post("/generation", json=body)
    assert response.status_code == status
    assert client.get("/generation").status_code == 404


def test_http_generation_rejects_a_second_run_while_busy(source: InspectionSource) -> None:
    save_demand(source)
    solve = HeldSolve()
    generation = Generation(read_input=source.service.read_generation_input, solve=solve, on_solved=Review().generated)
    app.dependency_overrides[get_generation] = lambda: generation
    try:
        client = cast(httpx.Client, TestClient(app))
        assert client.post("/generation", json=BODY).status_code == 202
        busy = client.post("/generation", json=BODY)
        assert busy.status_code == 423
        assert "running" in busy.json()["detail"]
        assert client.get("/generation").json()["state"] == "running"
    finally:
        solve.release.set()
        app.dependency_overrides.clear()
    assert finished(generation).state == JobState.COMPLETED


def test_http_generation_forgets_jobs_on_restart(source: InspectionSource) -> None:
    save_demand(source)
    solve = HeldSolve()
    solve.release.set()
    before = Generation(read_input=source.service.read_generation_input, solve=solve, on_solved=Review().generated)
    after = Generation(read_input=source.service.read_generation_input, solve=solve, on_solved=Review().generated)
    client = cast(httpx.Client, TestClient(app))
    try:
        app.dependency_overrides[get_generation] = lambda: before
        assert client.post("/generation", json=BODY).status_code == 202
        finished(before)
        # A restarted API process starts with a new, empty job state.
        app.dependency_overrides[get_generation] = lambda: after
        restarted = client.get("/generation")
        assert restarted.status_code == 404
        assert "restarts" in restarted.json()["detail"]
    finally:
        app.dependency_overrides.clear()
