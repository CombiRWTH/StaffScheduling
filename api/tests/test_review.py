"""Review tables, portable bundles, their published schemas and the review HTTP flow."""

import csv
import io
import json
from collections.abc import Callable, Iterator
from datetime import date
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from fastapi.testclient import TestClient
from inspection_fixture import InspectionSource
from scheduling import EARLY, JUMPER_POOL, NIGHT, NORTH, account, dataset, duty, jan, member, need
from test_generation import BODY, CONFIGURATION, INFEASIBLE, finished, save_demand

from app.api.generation import get_generation
from app.api.review import get_review
from app.domain import (
    Assignment,
    CheckStatus,
    CoverageRow,
    Gap,
    PlanningMonth,
    PlanningUnitMembership,
    PublicationRequest,
    SchedulingDataset,
    StaffLevel,
    check_schedule,
    schedule_tables,
)
from app.main import app
from app.settings import Settings
from app.solver.bundle import (
    COVERAGE_FILE,
    EMPLOYEES_FILE,
    GAPS_FILE,
    INPUT_FILE,
    RESULT_FILE,
    SCHEDULE_FILE,
    BundleProblem,
    FileName,
    InvalidBundle,
    ScheduleBundle,
    ScheduleInput,
    ScheduleResult,
    to_json,
)
from app.solver.generation import Generation
from app.solver.models import Solution, SolutionStatus, StageReport
from app.solver.review import Review
from app.solver.service import SolverService

ASSISTANT = StaffLevel.ASSISTANT
FEBRUARY = PlanningMonth(year=2026, month=2)
SCHEMA = Path(__file__).parents[2] / "docs/source/validation/schema"


def january() -> SchedulingDataset:
    """A station employee, a jumper pool employee and an assistant without duties."""
    return dataset(
        memberships=(
            *member(1),
            *member(2, home=JUMPER_POOL, replacements=(NORTH,)),
            *member(3, ASSISTANT),
        ),
        accounts=(account(1, 420), account(2, 555), account(3, 0)),
        demand=(need(jan(30), EARLY),),
        levels={3: ASSISTANT},
    )


# An early duty on Friday and a jumper pool employee's night from Saturday into February.
JANUARY_DUTIES = (duty(1, jan(30), EARLY), duty(2, jan(31), NIGHT))


def found(data: SchedulingDataset, assignments: tuple[Assignment, ...], gaps: tuple[Gap, ...] = ()) -> Solution:
    return Solution(
        status=SolutionStatus.OPTIMAL,
        configuration=CONFIGURATION,
        wall_time_seconds=1.5,
        assignments=assignments,
        gaps=gaps,
        stages=(StageReport(name="health_events", status=SolutionStatus.OPTIMAL, value=0, best_bound=0),),
        check=check_schedule(data, assignments, gaps),
    )


def bundle_of(
    data: SchedulingDataset, assignments: tuple[Assignment, ...], gaps: tuple[Gap, ...] = ()
) -> ScheduleBundle:
    schedule_input = ScheduleInput.of(data)
    return ScheduleBundle.solved(schedule_input, to_json(schedule_input), found(data, assignments, gaps))


def csv_rows(content: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(content.decode())))


def test_tables_label_duties_with_real_times_origin_and_every_employee() -> None:
    tables = schedule_tables(january(), JANUARY_DUTIES)

    early, night = tables.duties
    assert (early.employee_name, early.weekday, early.is_public_holiday, early.planning_unit_name) == (
        "Example 1",
        5,
        False,
        "North",
    )
    assert (early.origin_unit_id, early.origin_unit_type) == (NORTH, "station")
    # The night belongs to its start date and ends on February 1; the jumper pool employee works at North.
    assert (night.date, night.start_at.isoformat(), night.end_at.isoformat()) == (
        jan(31),
        "2026-01-31T20:10:00+01:00",
        "2026-02-01T06:10:00+01:00",
    )
    assert (night.planning_unit_id, night.origin_unit_id, night.origin_unit_type) == (NORTH, JUMPER_POOL, "jumper_pool")
    # Every participant has a row; the balance is generated plus credited minus target minutes.
    assert [(row.employee_id, row.generated_minutes, row.balance_minutes) for row in tables.employees] == [
        (1, 420, 0),
        (2, 555, 0),
        (3, 0, 0),
    ]
    # Demand is shown against the assigned staff, also where nobody was required.
    assert [(row.date.day, row.shift_id, row.required_count, row.assigned_count) for row in tables.staffing] == [
        (30, EARLY.shift_id, 1, 1),
        (31, NIGHT.shift_id, 0, 1),
    ]


def test_duty_origin_is_the_home_unit_of_its_date() -> None:
    # Employee 1 moves home from North to the jumper pool on January 16 and keeps working at North.
    before, after = (
        PlanningUnitMembership(
            planning_unit_id=unit,
            employee_id=1,
            valid_from=start,
            valid_until=end,
            staff_level=StaffLevel.PROFESSIONAL,
            is_home=True,
            is_replacement=False,
        )
        for unit, start, end in ((NORTH, date(2025, 12, 1), jan(15)), (JUMPER_POOL, jan(16), date(2026, 12, 31)))
    )
    replacement = member(1, home=JUMPER_POOL, replacements=(NORTH,))[1]
    data = dataset(memberships=(before, after, replacement), accounts=(account(1, 0),))

    tables = schedule_tables(data, (duty(1, jan(15), EARLY), duty(1, jan(16), EARLY)))
    home, transfer = tables.duties

    assert (home.planning_unit_id, home.origin_unit_id) == (NORTH, NORTH)
    assert (transfer.planning_unit_id, transfer.origin_unit_id, transfer.origin_unit_type) == (
        NORTH,
        JUMPER_POOL,
        "jumper_pool",
    )
    # The employee's month names the home of its first date; the memberships cell holds both intervals.
    assert (tables.employees[0].home_unit_id, tables.employees[0].home_unit_type) == (NORTH, "station")


def test_tables_follow_the_clock_change_and_mark_public_holidays() -> None:
    march = PlanningMonth(year=2026, month=3)
    data = dataset(memberships=member(1), accounts=(account(1, 0, month=march),), month=march)
    april = PlanningMonth(year=2026, month=4)
    holiday = dataset(memberships=member(1), accounts=(account(1, 0, month=april),), month=april)

    [night] = schedule_tables(data, (duty(1, date(2026, 3, 28), NIGHT),)).duties
    [good_friday] = schedule_tables(holiday, (duty(1, date(2026, 4, 3), EARLY),)).duties

    assert (night.start_at.isoformat(), night.end_at.isoformat()) == (
        "2026-03-28T20:10:00+01:00",
        "2026-03-29T06:10:00+02:00",
    )
    assert (good_friday.weekday, good_friday.is_public_holiday) == (5, True)


def test_bundle_files_carry_every_field_and_read_back() -> None:
    bundle = bundle_of(january(), JANUARY_DUTIES)
    files = bundle.files

    again = ScheduleBundle.read(files[INPUT_FILE], files[RESULT_FILE])
    assert again.files == files
    assert again.result.input.sha256 == bundle.result.input.sha256
    document = json.loads(files[INPUT_FILE])
    assert set(document) == {"format_version", "timezone", "calendar", "dataset"}
    # The canonical dataset only: no plan, special capability or derived field.
    assert set(document["dataset"]) == {
        "planning_month",
        "planning_units",
        "shifts",
        "demand_requirements",
        "employees",
        "planning_unit_memberships",
        "availability",
        "wishes",
        "monthly_work_accounts",
        "context",
    }
    assert document["dataset"]["planning_month"] == {"year": 2026, "month": 1}
    assert len(document["calendar"]) == 31

    schedule = csv_rows(files[SCHEDULE_FILE])
    assert list(schedule[0]) == [
        "employee_id",
        "employee_name",
        "date",
        "weekday",
        "is_public_holiday",
        "planning_unit_id",
        "planning_unit_name",
        "shift_id",
        "shift_code",
        "shift_type",
        "start_at",
        "end_at",
        "net_work_minutes",
        "staff_level",
        "qualifikation",
        "origin_unit_id",
        "origin_unit_name",
        "origin_unit_type",
    ]
    assert schedule[1] == {
        "employee_id": "2",
        "employee_name": "Example 2",
        "date": "2026-01-31",
        "weekday": "6",
        "is_public_holiday": "false",
        "planning_unit_id": str(NORTH),
        "planning_unit_name": "North",
        "shift_id": str(NIGHT.shift_id),
        "shift_code": "N",
        "shift_type": "night",
        "start_at": "2026-01-31T20:10:00+01:00",
        "end_at": "2026-02-01T06:10:00+01:00",
        "net_work_minutes": "555",
        "staff_level": "professional",
        "qualifikation": "Fachkraft",
        "origin_unit_id": str(JUMPER_POOL),
        "origin_unit_name": "Jumper pool",
        "origin_unit_type": "jumper_pool",
    }

    employees = csv_rows(files[EMPLOYEES_FILE])
    assert [row["employee_id"] for row in employees] == ["1", "2", "3"]
    jumper = employees[1]
    assert (jumper["home_unit_id"], jumper["home_unit_name"], jumper["home_unit_type"]) == (
        str(JUMPER_POOL),
        "Jumper pool",
        "jumper_pool",
    )
    assert (jumper["planning_month"], jumper["target_minutes"], jumper["generated_minutes"]) == (
        "2026-01",
        "555",
        "555",
    )
    # Multi-valued facts are complete JSON arrays inside quoted cells.
    memberships = json.loads(jumper["memberships"])
    assert [(row["planning_unit_id"], row["is_home"], row["is_replacement"]) for row in memberships] == [
        (JUMPER_POOL, True, False),
        (NORTH, False, True),
    ]
    assert json.loads(jumper["hard_availability"]) == []
    assert json.loads(employees[0]["credit_details"]) == []


def test_coverage_counts_each_demanded_qualification_and_gaps_are_its_missing_rows() -> None:
    # North needs a Fachkraft and a Hilfskraft for the early of January 30; only the Fachkraft is assigned.
    # The jumper pool employee's night of January 31 meets no demand, so it is a duty without coverage row.
    data = dataset(
        memberships=(*member(1), *member(2, home=JUMPER_POOL, replacements=(NORTH,)), *member(3, ASSISTANT)),
        accounts=(account(1, 420), account(2, 555), account(3, 0)),
        demand=(need(jan(30), EARLY), need(jan(30), EARLY, level=ASSISTANT)),
        levels={3: ASSISTANT},
    )
    missing = Gap(planning_unit_id=NORTH, date=jan(30), shift_id=EARLY.shift_id, staff_level=ASSISTANT, missing_count=1)
    files = bundle_of(data, JANUARY_DUTIES, (missing,)).files

    coverage = csv_rows(files[COVERAGE_FILE])
    early = {
        "planning_unit_id": str(NORTH),
        "planning_unit_name": "North",
        "date": "2026-01-30",
        "shift_id": str(EARLY.shift_id),
        "shift_code": "F",
    }
    assert coverage == [
        {
            **early,
            "staff_level": "assistant",
            "qualifikation": "Hilfskraft",
            "required_count": "1",
            "assigned_count": "0",
            "missing_count": "1",
        },
        {
            **early,
            "staff_level": "professional",
            "qualifikation": "Fachkraft",
            "required_count": "1",
            "assigned_count": "1",
            "missing_count": "0",
        },
    ]
    assert csv_rows(files[GAPS_FILE]) == coverage[:1]


def _set(path: str, value: Any) -> Callable[[dict[str, Any]], None]:
    """Replace one value of a JSON document, addressed by dotted keys and list indexes."""

    def change(document: dict[str, Any]) -> None:
        *parents, last = (int(key) if key.isdigit() else key for key in path.split("."))
        target: Any = document
        for key in parents:
            target = target[key]
        target[last] = value

    return change


def _edit(content: bytes, change: Callable[[dict[str, Any]], None]) -> bytes:
    document = json.loads(content)
    change(document)
    return json.dumps(document).encode()


def test_gaps_round_trip_and_an_undeclared_gap_is_no_bundle() -> None:
    # Employee 1 leaves the required early of January 30 open, within the balance band.
    missing = Gap(
        planning_unit_id=NORTH,
        date=jan(30),
        shift_id=EARLY.shift_id,
        staff_level=StaffLevel.PROFESSIONAL,
        missing_count=1,
    )
    files = bundle_of(january(), (duty(2, jan(31), NIGHT),), (missing,)).files

    assert csv_rows(files[GAPS_FILE]) == [
        {
            "planning_unit_id": str(NORTH),
            "planning_unit_name": "North",
            "date": "2026-01-30",
            "shift_id": str(EARLY.shift_id),
            "shift_code": "F",
            "staff_level": "professional",
            "qualifikation": "Fachkraft",
            "required_count": "1",
            "assigned_count": "0",
            "missing_count": "1",
        }
    ]
    imported = ScheduleBundle.read(files[INPUT_FILE], files[RESULT_FILE])
    assert imported.result.solution.gaps == (missing,)
    assert imported.check.status == CheckStatus.ACCEPTED
    assert imported.files == files
    # Publication writes the duties only; a gap is never a duty.
    review = Review()
    shown = review.imported(files[INPUT_FILE], files[RESULT_FILE])
    request = PublicationRequest(
        planning_month=shown.planning_month, planning_unit_ids=shown.station_ids, received_at=shown.received_at
    )
    assert review.publishable(request) == (duty(2, jan(31), NIGHT),)
    # Without gaps the header stays.
    assert bundle_of(january(), JANUARY_DUTIES).files[GAPS_FILE].decode().splitlines() == [
        ",".join(CoverageRow.model_fields)
    ]
    # A result that hides the gap carries a stale check, so it is no bundle.
    hidden = json.loads(files[RESULT_FILE])
    hidden["solution"]["gaps"] = []
    with pytest.raises(InvalidBundle) as error:
        ScheduleBundle.read(files[INPUT_FILE], json.dumps(hidden).encode())
    assert error.value.problem == BundleProblem.CHECK


@pytest.mark.parametrize(
    ("file", "change", "problem", "message"),
    [
        (INPUT_FILE, None, BundleProblem.MALFORMED, "input.json is invalid at top level"),
        (INPUT_FILE, _set("format_version", 1), BundleProblem.MALFORMED, "format_version"),
        (INPUT_FILE, _set("dataset.plan_id", 7), BundleProblem.MALFORMED, "plan_id: Extra inputs"),
        (INPUT_FILE, _set("calendar.0.public_holiday", None), BundleProblem.MALFORMED, "NRW calendar"),
        (INPUT_FILE, _set("dataset.monthly_work_accounts.2.target_minutes", 60), BundleProblem.MISMATCH, "another"),
        (RESULT_FILE, _set("planning_month.month", 2), BundleProblem.MISMATCH, "another planning month"),
        (RESULT_FILE, _set("solution.assignments.0.employee_id", 99), BundleProblem.REFERENCES, "unknown"),
        (RESULT_FILE, _set("solution.assignments.1.date", "2026-02-01"), BundleProblem.REFERENCES, "outside"),
        (RESULT_FILE, _set("solution.check.status", "rejected"), BundleProblem.CHECK, "differs from a re-check"),
        (RESULT_FILE, _set("solution.configuration.policy.min_rest_minutes", 600), BundleProblem.POLICY, "rule"),
    ],
)
def test_read_rejects_malformed_unknown_or_mismatched_files(
    file: FileName, change: Callable[[dict[str, Any]], None] | None, problem: BundleProblem, message: str
) -> None:
    files = dict(bundle_of(january(), JANUARY_DUTIES).files)
    files[file] = b"[" if change is None else _edit(files[file], change)

    with pytest.raises(InvalidBundle, match=message) as raised:
        ScheduleBundle.read(files[INPUT_FILE], files[RESULT_FILE])
    assert raised.value.problem == problem


def test_read_rejects_a_result_without_schedule() -> None:
    bundle = bundle_of(january(), JANUARY_DUTIES)
    result = bundle.result.model_copy(update={"solution": INFEASIBLE})

    with pytest.raises(InvalidBundle, match="no schedule") as raised:
        ScheduleBundle.read(bundle.input_json, to_json(result))
    assert raised.value.problem == BundleProblem.NO_SCHEDULE


def test_published_schemas_are_the_model_schemas() -> None:
    """A stale schema is rewritten from its model, so the next run passes once the change is committed."""
    stale: list[str] = []
    for name, model in (("input.schema.json", ScheduleInput), ("result.schema.json", ScheduleResult)):
        schema = json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n"
        if not (SCHEMA / name).is_file() or (SCHEMA / name).read_text() != schema:
            (SCHEMA / name).write_text(schema)
            stale.append(name)
    assert not stale, f"Rewrote the stale {stale} in {SCHEMA}; review and commit them."


@pytest.fixture
def review() -> Review:
    return Review()


@pytest.fixture
def client(review: Review) -> Iterator[tuple[httpx.Client, Generation, InspectionSource]]:
    source = InspectionSource()
    save_demand(source)
    solver = SolverService(Settings(solver_num_search_workers=1))
    generation = Generation(
        read_input=source.service.read_generation_input,
        solve=lambda dataset, timeout: solver.solve(dataset, timeout=min(timeout, 2)),
        on_solved=review.generated,
    )
    app.dependency_overrides[get_generation] = lambda: generation
    app.dependency_overrides[get_review] = lambda: review
    try:
        yield cast(httpx.Client, TestClient(app)), generation, source
    finally:
        app.dependency_overrides.clear()
        generation.shutdown()


@pytest.mark.integration
def test_http_review_downloads_and_imports_only_valid_pairs(
    client: tuple[httpx.Client, Generation, InspectionSource],
) -> None:
    http, generation, _ = client
    assert http.get("/review").status_code == 404
    assert http.get(f"/review/files/{INPUT_FILE}").status_code == 404

    http.post("/generation", json=BODY)
    finished(generation)
    generated = http.get("/review").json()
    assert generated["source"] == "generation"
    assert generated["solution"]["check"]["status"] == "accepted"
    assert len(generated["tables"]["duties"]) == len(generated["solution"]["assignments"])
    # Employee 3 has no duties and is still part of the review.
    assert {row["employee_id"] for row in generated["tables"]["employees"]} == {1, 2, 3}

    files: dict[str, bytes] = {}
    json_type, csv_type = "application/json", "text/csv; charset=utf-8"
    for name, media_type in (
        (INPUT_FILE, json_type),
        (RESULT_FILE, json_type),
        (SCHEDULE_FILE, csv_type),
        (EMPLOYEES_FILE, csv_type),
        (GAPS_FILE, csv_type),
        (COVERAGE_FILE, csv_type),
    ):
        response = http.get(f"/review/files/{name}")
        assert response.status_code == 200
        assert response.headers["content-type"] == media_type
        assert response.headers["content-disposition"] == f'attachment; filename="{name}"'
        files[name] = response.content

    def upload(input_json: bytes, result_json: bytes) -> httpx.Response:
        return http.post(
            "/review/import",
            files={"input": (INPUT_FILE, input_json), "result": (RESULT_FILE, result_json)},
        )

    imported = upload(files[INPUT_FILE], files[RESULT_FILE])
    assert imported.status_code == 200
    assert imported.json()["source"] == "import"
    assert imported.json()["tables"] == generated["tables"]

    other_input = _edit(files[INPUT_FILE], _set("dataset.monthly_work_accounts.0.target_minutes", 1))
    rejected = upload(other_input, files[RESULT_FILE])
    assert rejected.status_code == 422
    assert rejected.json()["problem"] == "mismatch"
    # The rejected pair leaves the imported review and its files in place.
    assert http.get("/review").json()["received_at"] == imported.json()["received_at"]
    assert http.get(f"/review/files/{SCHEDULE_FILE}").content == files[SCHEDULE_FILE]
