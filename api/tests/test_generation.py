from collections.abc import Iterator
from threading import Event
from time import monotonic, sleep
from typing import cast

import httpx
import pytest
from fastapi.testclient import TestClient
from inspection_fixture import InspectionSource

from app.api.generation import get_generation
from app.domain import (
    DemandCell,
    InvalidSelection,
    MonthlyDemand,
    PlanningMonth,
    SchedulingDataset,
    ShiftType,
    StaffingDemandRole,
    StaffLevel,
)
from app.main import app
from app.settings import Settings
from app.solver.cp_sat.builder import create_cp_sat_model_builder
from app.solver.generation import Generation, GenerationBusy, GenerationJob, GenerationRequest, JobState
from app.solver.models import Solution, SolutionStatus
from app.solver.service import SolverService

JANUARY = PlanningMonth(year=2026, month=1)
REQUEST = GenerationRequest(planning_unit_ids=(101,), planning_month=JANUARY, timeout_seconds=5)
EARLY = 1113
INFEASIBLE = Solution(status=SolutionStatus.INFEASIBLE)


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
    return SchedulingDataset(planning_month=JANUARY, planning_units=(), plans=())


def test_generation_accepts_at_once_rejects_overlap_and_releases_after_finishing() -> None:
    solve = HeldSolve()
    generation = Generation(read_input=read_nothing, solve=solve)

    job = generation.start(REQUEST)
    assert solve.started.wait(5)
    assert job.state == JobState.RUNNING
    assert generation.latest() == job
    with pytest.raises(GenerationBusy):
        generation.start(REQUEST)

    solve.release.set()
    done = finished(generation)
    assert (done.job_id, done.state, done.acceptance) == (job.job_id, JobState.COMPLETED, "not_assessed")
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
    generation = Generation(read_input=read_nothing, solve=solve)

    generation.start(REQUEST)
    failed = finished(generation)
    assert failed.state == JobState.FAILED
    assert failed.solution is None
    assert failed.error
    assert "internal details" not in failed.error

    def invalid(**_: object) -> SchedulingDataset:
        raise InvalidSelection("not plannable")

    rejecting = Generation(read_input=invalid, solve=solve)
    with pytest.raises(InvalidSelection):
        rejecting.start(REQUEST)
    assert rejecting.latest() is None
    rejecting = Generation(read_input=read_nothing, solve=solve)
    assert rejecting.start(REQUEST).state == JobState.RUNNING
    finished(rejecting)


def test_generation_input_reads_only_absences_from_the_roster() -> None:
    source = InspectionSource()
    with pytest.raises(ValueError, match="No saved staffing demand"):
        source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY)
    save_demand(source)
    source.queries.clear()

    dataset = source.service.read_generation_input(planning_unit_ids=(101, 101), planning_month=JANUARY)

    # Polluted worked shifts (another plan, earlier output in the target plan) never become input.
    assert dataset.assignments == ()
    roster_queries = [sql for sql in source.queries if "TPlanPersonalKommtGeht" in sql]
    assert roster_queries
    assert not any("pkg.RefDienste " in sql or "pkg.RefDienste\n" in sql for sql in roster_queries)
    # The approved absence still binds planning.
    assert [(row.employee_id, row.date.day, row.reason) for row in dataset.availability] == [(1, 1, "U")]
    # Station 101 is assignable, pool 201 is origin context; station 102 stays out of this run.
    assert [unit.planning_unit_id for unit in dataset.planning_units] == [101, 201]
    assert {row.planning_unit_id for row in dataset.planning_unit_memberships} == {101, 201}
    assert {row.planning_unit_id for row in dataset.demand_requirements} == {101}
    assert len(dataset.demand_requirements) == 2
    assert len(dataset.monthly_work_accounts) == 3
    assert dataset.wishes == ()
    assert dataset.plans == ()
    assert all(employee.capabilities == () for employee in dataset.employees)


def test_generation_input_times_the_reference_shifts() -> None:
    source = InspectionSource()
    save_demand(source)
    shifts = source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY).shifts

    assert [(s.code, s.type, s.start_minute, s.end_minute, s.net_work_minutes) for s in shifts] == [
        ("F", ShiftType.EARLY, 355, 805, 420),
        # A segment without paid minutes counts its full length.
        ("Z", ShiftType.INTERMEDIATE, 510, 855, 345),
        ("S", ShiftType.LATE, 795, 1260, 435),
        ("N", ShiftType.NIGHT, 1210, 370, 555),
    ]
    assert [s.staffing_role for s in shifts].count(StaffingDemandRole.OPTIONAL_COVERAGE) == 1

    source.missing_shift_times = True
    with pytest.raises(ValueError, match="Missing TimeOffice shift times"):
        source.service.read_generation_input(planning_unit_ids=(101,), planning_month=JANUARY)


@pytest.fixture
def source() -> InspectionSource:
    return InspectionSource()


@pytest.fixture
def generation(source: InspectionSource) -> Iterator[Generation]:
    solver = SolverService(Settings(solver_num_search_workers=1), create_cp_sat_model_builder())
    generation = Generation(read_input=source.service.read_generation_input, solve=solver.solve)
    yield generation
    generation.shutdown()


@pytest.fixture
def client(generation: Generation) -> Iterator[httpx.Client]:
    app.dependency_overrides[get_generation] = lambda: generation
    try:
        yield cast(httpx.Client, TestClient(app))
    finally:
        app.dependency_overrides.clear()


BODY = {"planning_unit_ids": [101], "planning_month": {"year": 2026, "month": 1}, "timeout_seconds": 5}


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
    assert job["acceptance"] == "not_assessed"
    assert job["solution"]["status"] in {status.value for status in SolutionStatus}
    for assignment in job["solution"]["assignments"]:
        assert assignment["planning_unit_id"] == 101
        assert assignment["assignment_type"] == "generated"


@pytest.mark.parametrize(
    ("body", "status"),
    [
        ({**BODY, "timeout_seconds": 0}, 422),
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
    generation = Generation(read_input=source.service.read_generation_input, solve=solve)
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
    before = Generation(read_input=source.service.read_generation_input, solve=solve)
    after = Generation(read_input=source.service.read_generation_input, solve=solve)
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
