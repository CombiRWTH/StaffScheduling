"""Publication of the reviewed schedule into the stations' target plans, and the explicit clear."""

import copy
from collections.abc import Iterator
from datetime import datetime
from threading import Event, Thread
from time import sleep
from typing import Any, cast

import httpx
import pytest
from fastapi.testclient import TestClient
from inspection_fixture import PROFESSION_IDS, InspectionSource
from test_generation import BODY, finished, save_demand

from app.api.generation import get_generation
from app.api.review import get_review
from app.api.shared import get_planning_source
from app.domain import (
    Assignment,
    InvalidSelection,
    PlanningMonth,
    PublicationProblem,
    PublicationRejected,
    PublicationResult,
    StaffLevel,
)
from app.main import app
from app.settings import Settings
from app.solver.generation import Generation
from app.solver.review import Review
from app.solver.service import SolverService
from app.timeoffice import TimeOfficeConflict, TimeOfficeUnavailable
from app.timeoffice.facts import GENERATED_DUTY_INFO

JANUARY = PlanningMonth(year=2026, month=1)
EARLY, NIGHT = 1113, 1690
NORTH, SOUTH, JUMPER_POOL = 101, 102, 201
NORTH_PLAN, SOUTH_PLAN = 1101, 1102
STATIONS = (NORTH, SOUTH)
PROFESSIONAL, MFA = PROFESSION_IDS["81302-028"], PROFESSION_IDS["81102-004"]

TEAM_EARLY = Assignment(
    employee_id=2,
    date=JANUARY.start.replace(day=5),
    planning_unit_id=NORTH,
    shift_id=EARLY,
    staff_level=StaffLevel.PROFESSIONAL,
)
# Employee 1 is from the jumper pool and stands in at South; the night ends on January 7.
JUMPER_NIGHT = Assignment(
    employee_id=1, date=JANUARY.start.replace(day=6), planning_unit_id=SOUTH, shift_id=NIGHT, staff_level=StaffLevel.MFA
)
SCHEDULE = (TEAM_EARLY, JUMPER_NIGHT)


def roster_row(plan_id: int, employee_id: int, day: int, number: int = 1, **fields: Any) -> dict[str, Any]:
    """A roster row of January, by default an early duty segment of employee 2 at North."""
    return {
        "plan_id": plan_id,
        "employee_id": employee_id,
        "roster_date": datetime(2026, 1, day),
        "status_id": 20,
        "number": number,
        "shift_id": EARLY,
        "profession_id": PROFESSIONAL,
        "planning_unit_id": NORTH,
        "segment_start": datetime(2026, 1, day, 5, 55),
        "segment_end": datetime(2026, 1, day, 10),
        "minutes": 245,
        **fields,
    }


# Rows publication must keep: a native wish, an absence and a duty entered in TimeOffice in North's target,
# and a duty in another plan.
WISH = roster_row(NORTH_PLAN, 2, 5, wish=True, shift_id=NIGHT)
ABSENCE = roster_row(NORTH_PLAN, 2, 20, absence="U", shift_id=None, minutes=0)
ENTERED_DUTY = roster_row(NORTH_PLAN, 2, 14)
OTHER_PLAN_DUTY = roster_row(9, 2, 12, planning_unit_id=999)
# Earlier published output in North's target, which publication replaces.
EARLIER_OUTPUT = roster_row(NORTH_PLAN, 2, 9, info=GENERATED_DUTY_INFO)
KEPT = [WISH, ABSENCE, ENTERED_DUTY, OTHER_PLAN_DUTY]


@pytest.fixture
def source() -> InspectionSource:
    source = InspectionSource()
    source.roster = [copy.deepcopy(row) for row in (*KEPT, EARLIER_OUTPUT)]
    return source


def publish(
    source: InspectionSource, assignments: tuple[Assignment, ...] = SCHEDULE, stations: tuple[int, ...] = STATIONS
) -> PublicationResult:
    return source.service.publish(planning_month=JANUARY, planning_unit_ids=stations, assignments=assignments)


def output(source: InspectionSource) -> list[dict[str, Any]]:
    return [row for row in source.roster if InspectionSource.is_output(row, [NORTH_PLAN, SOUTH_PLAN])]


def kept(source: InspectionSource) -> list[dict[str, Any]]:
    return [row for row in source.roster if not InspectionSource.is_output(row, [NORTH_PLAN, SOUTH_PLAN])]


@pytest.mark.integration
def test_publication_writes_each_segment_into_the_destination_target_and_keeps_other_rows(
    source: InspectionSource,
) -> None:
    result = publish(source)

    assert (result.removed_duties, result.published_duties) == (1, 2)
    assert kept(source) == KEPT
    rows = {(row["employee_id"], row["number"]): row for row in output(source)}
    # The early duty is numbered after the native wish of that date and books the team profession.
    early = [rows[(2, 2)], rows[(2, 3)]]
    assert [(row["segment_start"].hour, row["segment_end"].hour, row["minutes"]) for row in early] == [
        (5, 10, 245),
        (10, 13, 175),
    ]
    assert {(row["plan_id"], row["planning_unit_id"], row["profession_id"]) for row in early} == {
        (NORTH_PLAN, NORTH, PROFESSIONAL)
    }
    # The jumper's night goes to South's target with the profession of their South membership; its
    # segments keep the start date and the last one ends on the next day.
    night = [rows[(1, number)] for number in (1, 2, 3)]
    assert {(row["plan_id"], row["planning_unit_id"], row["profession_id"]) for row in night} == {
        (SOUTH_PLAN, SOUTH, MFA)
    }
    assert {row["roster_date"] for row in night} == {datetime(2026, 1, 6)}
    assert night[-1]["segment_end"] == datetime(2026, 1, 7, 6, 10)
    assert sum(row["minutes"] for row in night) == 555


@pytest.mark.integration
def test_invalid_or_conflicting_schedules_fail_before_anything_is_deleted(source: InspectionSource) -> None:
    before = copy.deepcopy(source.roster)
    absent = TEAM_EARLY.model_copy(update={"date": JANUARY.start.replace(day=20)})
    elsewhere = TEAM_EARLY.model_copy(update={"date": JANUARY.start.replace(day=12)})
    entered = TEAM_EARLY.model_copy(update={"date": JANUARY.start.replace(day=14)})
    for assignments, error in (
        ((), InvalidSelection),
        ((TEAM_EARLY.model_copy(update={"planning_unit_id": SOUTH}),), ValueError),  # no South membership
        ((TEAM_EARLY.model_copy(update={"staff_level": StaffLevel.ASSISTANT}),), ValueError),
        ((TEAM_EARLY.model_copy(update={"date": PlanningMonth(year=2026, month=2).start}),), InvalidSelection),
        ((TEAM_EARLY.model_copy(update={"shift_id": 9999}),), InvalidSelection),
        ((TEAM_EARLY, TEAM_EARLY.model_copy(update={"planning_unit_id": SOUTH})), InvalidSelection),
    ):
        with pytest.raises(error):
            publish(source, assignments)
    for assignments in ((absent,), (elsewhere,), (entered,)):
        with pytest.raises(PublicationRejected) as rejected:
            publish(source, assignments)
        assert rejected.value.problem == PublicationProblem.CONFLICT
    # The duty is only valid for the named stations.
    with pytest.raises(InvalidSelection):
        publish(source, SCHEDULE, stations=(NORTH,))
    assert source.roster == before


@pytest.mark.integration
def test_failed_colliding_or_misread_writes_roll_back_the_deletion(source: InspectionSource) -> None:
    before = copy.deepcopy(source.roster)
    source.failing_ids = {1}
    with pytest.raises(TimeOfficeUnavailable):
        publish(source)
    source.failing_ids, source.conflicting_ids = set(), {1}
    with pytest.raises(TimeOfficeConflict):
        publish(source)
    source.conflicting_ids, source.losing_published_duty = set(), True
    with pytest.raises(PublicationRejected) as rejected:
        publish(source)
    assert rejected.value.problem == PublicationProblem.READ_BACK
    assert source.roster == before


@pytest.mark.integration
def test_a_failed_commit_reports_an_unknown_outcome(source: InspectionSource) -> None:
    source.failing_commit = True
    with pytest.raises(TimeOfficeUnavailable) as failed:
        publish(source)
    assert failed.value.stage == "commit"


@pytest.mark.integration
def test_targets_must_exist_once_for_the_named_stations(source: InspectionSource) -> None:
    before = copy.deepcopy(source.roster)
    source.duplicate_plan = True
    with pytest.raises(ValueError, match="Multiple TimeOffice target plans"):
        publish(source)
    with pytest.raises(ValueError, match="Multiple TimeOffice target plans"):
        source.service.clear(planning_month=JANUARY, planning_unit_ids=STATIONS)
    source.duplicate_plan = False
    february = PlanningMonth(year=2026, month=2)  # North has no target plan in February.
    for stations in ((NORTH,), (JUMPER_POOL,)):
        with pytest.raises(InvalidSelection):
            source.service.clear(planning_month=february, planning_unit_ids=stations)
    assert source.roster == before


@pytest.mark.integration
def test_clear_removes_only_the_named_stations_published_duties(source: InspectionSource) -> None:
    publish(source)

    south = source.service.clear(planning_month=JANUARY, planning_unit_ids=(SOUTH,))
    assert (south.removed_duties, south.published_duties) == (1, 0)
    assert {row["plan_id"] for row in output(source)} == {NORTH_PLAN}
    north = source.service.clear(planning_month=JANUARY, planning_unit_ids=(NORTH,))
    assert north.removed_duties == 1
    assert output(source) == []
    assert kept(source) == KEPT


@pytest.mark.integration
def test_publications_and_clears_are_serialized(source: InspectionSource) -> None:
    """A second write waits for the first, so target checks and row numbers never interleave."""
    inserting, release = Event(), Event()

    def hold() -> None:
        inserting.set()
        assert release.wait(5)

    source.before_roster_insert = hold
    first = Thread(target=publish, args=(source,))
    first.start()
    assert inserting.wait(5)
    statements = len(source.queries)
    second = Thread(target=source.service.clear, kwargs={"planning_month": JANUARY, "planning_unit_ids": STATIONS})
    second.start()
    sleep(0.2)
    assert len(source.queries) == statements
    release.set()
    first.join(5)
    second.join(5)
    assert output(source) == []
    assert kept(source) == KEPT


@pytest.fixture
def client(source: InspectionSource) -> Iterator[tuple[httpx.Client, Generation, InspectionSource]]:
    """The HTTP API over the fixture, with January demand at North and a real two-second solve."""
    source.roster = []
    save_demand(source)
    review = Review()
    solver = SolverService(Settings(solver_num_search_workers=1))
    generation = Generation(
        read_input=source.service.read_generation_input,
        solve=lambda dataset, timeout: solver.solve(dataset, timeout=min(timeout, 2)),
        on_solved=review.generated,
    )
    app.dependency_overrides[get_generation] = lambda: generation
    app.dependency_overrides[get_review] = lambda: review
    app.dependency_overrides[get_planning_source] = lambda: source.service
    try:
        yield cast(httpx.Client, TestClient(app)), generation, source
    finally:
        app.dependency_overrides.clear()
        generation.shutdown()


@pytest.mark.integration
def test_http_publishes_only_the_accepted_schedule_under_review_and_clears_explicitly(
    client: tuple[httpx.Client, Generation, InspectionSource],
) -> None:
    http, generation, source = client
    request = {"planning_month": {"year": 2026, "month": 1}, "planning_unit_ids": [NORTH]}
    nothing = http.post("/publication", json={**request, "received_at": "2026-01-01T00:00:00Z"})
    assert (nothing.status_code, nothing.json()["problem"]) == (409, "changed")

    http.post("/generation", json=BODY)
    finished(generation)
    review = http.get("/review").json()
    assert review["solution"]["check"]["status"] == "accepted"
    named = {**request, "received_at": review["received_at"]}
    for stale in ({**named, "received_at": "2026-01-01T00:00:00Z"}, {**named, "planning_unit_ids": [NORTH, SOUTH]}):
        response = http.post("/publication", json=stale)
        assert (response.status_code, response.json()["problem"]) == (409, "changed")
    assert source.roster == []

    # A duty entered in TimeOffice on a duty's date, a colliding writer and a failing database each change nothing.
    first = review["solution"]["assignments"][0]
    day = datetime.fromisoformat(first["date"]).day
    source.roster = [roster_row(NORTH_PLAN, first["employee_id"], day)]
    response = http.post("/publication", json=named)
    assert (response.status_code, response.json()["problem"]) == (409, "conflict")
    source.roster = []
    source.conflicting_ids = {NORTH}
    response = http.post("/publication", json=named)
    assert (response.status_code, response.json()["problem"]) == (409, "concurrent")
    source.conflicting_ids, source.failing_ids = set(), {NORTH}
    assert http.post("/publication", json=named).status_code == 503
    source.failing_ids = set()
    assert source.roster == []

    published = http.post("/publication", json=named)
    assert published.status_code == 200
    duties = len(review["solution"]["assignments"])
    assert (published.json()["removed_duties"], published.json()["published_duties"]) == (0, duties)
    again = http.post("/publication", json=named)
    assert (again.json()["removed_duties"], again.json()["published_duties"]) == (duties, duties)

    assert http.delete("/publication", params={"year": 2026, "month": 1}).status_code == 422
    assert (
        http.delete("/publication", params={"year": 2026, "month": 1, "planning_unit_ids": JUMPER_POOL}).status_code
        == 422
    )
    cleared = http.delete("/publication", params={"year": 2026, "month": 1, "planning_unit_ids": NORTH})
    assert cleared.status_code == 200
    assert (cleared.json()["removed_duties"], cleared.json()["published_duties"]) == (duties, 0)
    assert source.roster == []

    # Without trusted context the check cannot accept the next schedule, which is therefore not published.
    source.context_plans = False
    http.post("/generation", json=BODY)
    finished(generation)
    incomplete = http.get("/review").json()
    assert incomplete["solution"]["check"]["status"] == "incomplete"
    response = http.post("/publication", json={**request, "received_at": incomplete["received_at"]})
    assert (response.status_code, response.json()["problem"]) == (409, "not_accepted")
    assert source.roster == []
