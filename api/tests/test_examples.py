"""The hand-in examples: accepted monthly bundles of both example stations, January to June 2026.

`check_examples` validates monthly bundle folders; the committed `examples/` must pass it. The
`reproduction` tests solve every committed input again without TimeOffice and take minutes, so they
run only on request: `just test -m reproduction tests/test_examples.py`.
"""

from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path

import pytest
from pydantic import BaseModel
from scheduling import EARLY, JANUARY, JUMPER_POOL, NIGHT, NORTH, SOUTH, account, away, dataset, duty, jan, member, need
from test_review import FEBRUARY, bundle_of

from app.domain import Assignment, Availability, CheckStatus, DemandRequirement, PlanningMonth, SchedulingDataset
from app.settings import Settings
from app.solver.bundle import (
    EMPLOYEES_FILE,
    GAPS_FILE,
    INPUT_FILE,
    RESULT_FILE,
    SCHEDULE_FILE,
    InvalidBundle,
    ScheduleBundle,
)
from app.solver.service import SolverService

EXAMPLES = Path(__file__).parents[2] / "examples"
HAND_IN_MONTHS = tuple(PlanningMonth(year=2026, month=month) for month in range(1, 7))
HAND_IN_STATIONS = 2

# Temporary until the hand-in examples are committed: then delete this skip, so that a missing
# examples/ folder fails instead of passing silently.
committed = pytest.mark.skipif(not EXAMPLES.is_dir(), reason="the hand-in examples are not committed yet")


def check_examples(directory: Path, months: Sequence[PlanningMonth], stations: int) -> list[str]:
    """The problems of the folders `YYYY-MM` of `months` as hand-in examples; empty when they pass.

    Each folder must hold a complete bundle that reads like an import, renders back to its own files and
    is accepted by the schedule check. All months plan the same `stations` stations and jumper pools,
    every station has duties every month, and consecutive months agree on their shared context.
    """
    labels = [month.label for month in months]
    problems = [
        f"Folder outside {labels[0]} to {labels[-1]}: {path.name}."
        for path in sorted(directory.glob("????-??"))
        if path.name not in labels
    ]
    bundles = [_check_folder(directory / month.label, month, problems) for month in months]
    loaded = [bundle for bundle in bundles if bundle is not None]
    for bundle in loaded:
        data, first = bundle.input.dataset, loaded[0].input.dataset
        label = data.planning_month.label
        if data.planning_units != first.planning_units:
            problems.append(f"{label}: plans other stations or jumper pools than {first.planning_month.label}.")
        if len(data.station_ids) != stations:
            problems.append(f"{label}: {len(data.station_ids)} planned stations instead of {stations}.")
        if idle := sorted(data.station_ids - {row.planning_unit_id for row in bundle.result.solution.assignments}):
            problems.append(f"{label}: no duties at stations {idle}.")
    for earlier, later in zip(bundles, bundles[1:], strict=False):
        if earlier is not None and later is not None:
            problems.extend(_sequence_problems(earlier, later))
    return problems


def _check_folder(folder: Path, month: PlanningMonth, problems: list[str]) -> ScheduleBundle | None:
    label = month.label
    files = (INPUT_FILE, RESULT_FILE, SCHEDULE_FILE, EMPLOYEES_FILE, GAPS_FILE)
    if missing := [name for name in files if not (folder / name).is_file() or not (folder / name).stat().st_size]:
        problems.append(f"{label}: missing or empty {', '.join(missing)}.")
        return None
    try:
        bundle = ScheduleBundle.read((folder / INPUT_FILE).read_bytes(), (folder / RESULT_FILE).read_bytes())
    except InvalidBundle as error:
        problems.append(f"{label}: {error}")
        return None
    if bundle.input.dataset.planning_month != month:
        problems.append(f"{label}: the bundle plans {bundle.input.dataset.planning_month.label}.")
        return None
    problems.extend(
        f"{label}: {name} differs from the rendering of the pair."
        for name in (RESULT_FILE, SCHEDULE_FILE, EMPLOYEES_FILE, GAPS_FILE)
        if (folder / name).read_bytes() != bundle.files[name]
    )
    if (check := bundle.check).status != CheckStatus.ACCEPTED:
        blocking = sorted({row.rule.value for row in check.not_assessed if row.blocking})
        problems.append(
            f"{label}: diagnostic result, not an example: schedule check {check.status.value} with "
            f"{len(check.findings)} findings and blocking gaps in {blocking or 'no rule'}."
        )
    return bundle


def _sequence_problems(earlier: ScheduleBundle, later: ScheduleBundle) -> list[str]:
    """Each month's context duties on the other month's dates must be that month's schedule.

    Only employees of the context's own month can appear in its context; whether the context reaches far
    enough is the schedule check's concern, which blocks acceptance otherwise.
    """
    problems: list[str] = []
    label = f"{earlier.input.dataset.planning_month.label} to {later.input.dataset.planning_month.label}"
    for context, schedule in ((later, earlier), (earlier, later)):
        reader, month = context.input.dataset, schedule.input.dataset.planning_month
        employees = {row.employee_id for row in reader.employees}
        days = {day for day in month.dates if reader.context.covers(day)}
        trusted = _rows(row for row in reader.context.duties if row.date in days)
        scheduled = _rows(
            row for row in schedule.result.solution.assignments if row.date in days and row.employee_id in employees
        )
        if trusted != scheduled:
            problems.append(f"{label}: the context duties on {month.label} dates differ from its schedule.")
    before, after = earlier.input.dataset, later.input.dataset
    employees = {row.employee_id for row in before.employees}
    first = after.planning_month.start
    if _rows(before.context.availability) != _rows(
        row for row in after.availability if row.date == first and row.employee_id in employees
    ):
        problems.append(f"{label}: the availability of {first} differs between the two inputs.")
    return problems


def _rows(rows: Iterable[BaseModel]) -> set[str]:
    return {row.model_dump_json() for row in rows}


@committed
def test_committed_examples_are_accepted_hand_in_bundles() -> None:
    assert check_examples(EXAMPLES, HAND_IN_MONTHS, HAND_IN_STATIONS) == []


@pytest.mark.reproduction
@committed
@pytest.mark.parametrize("month", HAND_IN_MONTHS, ids=lambda month: month.label)
def test_committed_inputs_solve_again_to_accepted_schedules(month: PlanningMonth) -> None:
    """Byte-identical results are not expected; an equally valid schedule is."""
    folder = EXAMPLES / month.label
    input_json = (folder / INPUT_FILE).read_bytes()
    example = ScheduleBundle.read(input_json, (folder / RESULT_FILE).read_bytes())
    recorded = example.result.solution.configuration
    settings = Settings(solver_num_search_workers=recorded.search_workers, solver_random_seed=recorded.random_seed)

    solution = SolverService(settings).solve(example.input.dataset, recorded.timeout_seconds)

    assert ScheduleBundle.solved(example.input, input_json, solution).check.status == CheckStatus.ACCEPTED


def write_folder(directory: Path, bundle: ScheduleBundle) -> Path:
    folder = directory / bundle.input.dataset.planning_month.label
    folder.mkdir()
    for name, content in bundle.files.items():
        (folder / name).write_bytes(content)
    return folder


def two_stations(
    month: PlanningMonth,
    targets: dict[int, int],
    *,
    demand: tuple[DemandRequirement, ...] = (),
    context: tuple[Assignment, ...] = (),
    availability: tuple[Availability, ...] = (),
) -> SchedulingDataset:
    """North and South: a North employee, a jumper pool employee for North and a South employee."""
    return dataset(
        memberships=(*member(1), *member(2, home=JUMPER_POOL, replacements=(NORTH,)), *member(4, home=SOUTH)),
        accounts=tuple(account(employee_id, target, month=month) for employee_id, target in targets.items()),
        demand=demand,
        availability=availability,
        month=month,
        context_duties=context,
        covered_days_before=5,
    )


# January: early duties at both stations on Friday and a jumper pool employee's night into February.
NORTH_EARLY, SOUTH_EARLY = duty(1, jan(30), EARLY), duty(4, jan(30), EARLY, unit=SOUTH)
JANUARY_DUTIES = (NORTH_EARLY, SOUTH_EARLY, duty(2, jan(31), NIGHT))
FEBRUARY_DUTIES = (duty(1, date(2026, 2, 3), EARLY), duty(4, date(2026, 2, 3), EARLY, unit=SOUTH))


def january(duties: tuple[Assignment, ...] = JANUARY_DUTIES) -> ScheduleBundle:
    data = two_stations(
        JANUARY, {1: 420, 2: 555, 4: 420}, demand=(need(jan(30), EARLY), need(jan(30), EARLY, unit=SOUTH))
    )
    return bundle_of(data, duties)


def february(context: tuple[Assignment, ...] = JANUARY_DUTIES, availability: tuple[Availability, ...] = ()):
    """February with January 27-31 as trusted context."""
    data = two_stations(FEBRUARY, {1: 420, 2: 0, 4: 420}, context=context, availability=availability)
    return bundle_of(data, FEBRUARY_DUTIES)


def test_examples_accept_a_complete_consistent_sequence(tmp_path: Path) -> None:
    write_folder(tmp_path, january())
    write_folder(tmp_path, february())

    assert check_examples(tmp_path, (JANUARY, FEBRUARY), stations=2) == []


def test_examples_reject_drift_and_inconsistent_context(tmp_path: Path) -> None:
    write_folder(tmp_path, january())
    # February trusts only two of January's duties and holds an absence on its first date that January lacks.
    absent = away(1, FEBRUARY.start)
    february_folder = write_folder(tmp_path, february(JANUARY_DUTIES[:2], (absent,)))
    (tmp_path / "2026-03").mkdir()
    (february_folder / SCHEDULE_FILE).write_bytes(b"employee_id\n")

    assert check_examples(tmp_path, (JANUARY, FEBRUARY), stations=2) == [
        "Folder outside 2026-01 to 2026-02: 2026-03.",
        "2026-02: schedule.csv differs from the rendering of the pair.",
        "2026-01 to 2026-02: the context duties on 2026-01 dates differ from its schedule.",
        "2026-01 to 2026-02: the availability of 2026-02-01 differs between the two inputs.",
    ]


def test_examples_reject_diagnostics_other_scopes_and_unusable_folders(tmp_path: Path) -> None:
    # January without South's demanded duty is a diagnosis; February plans North alone.
    write_folder(tmp_path, january((NORTH_EARLY, JANUARY_DUTIES[2])))
    february_folder = write_folder(tmp_path, bundle_of(north_only(), FEBRUARY_DUTIES[:1]))

    assert check_examples(tmp_path, (JANUARY, FEBRUARY), stations=2) == [
        "2026-01: diagnostic result, not an example: schedule check rejected with 1 findings and blocking gaps "
        "in no rule.",
        f"2026-01: no duties at stations [{SOUTH}].",
        "2026-02: plans other stations or jumper pools than 2026-01.",
        "2026-02: 1 planned stations instead of 2.",
    ]

    for name, content in january().files.items():
        (february_folder / name).write_bytes(content)
    assert "2026-02: the bundle plans 2026-01." in check_examples(tmp_path, (JANUARY, FEBRUARY), stations=2)
    (february_folder / EMPLOYEES_FILE).write_bytes(b"")
    assert "2026-02: missing or empty employees.csv." in check_examples(tmp_path, (JANUARY, FEBRUARY), stations=2)


def north_only() -> SchedulingDataset:
    """February of North and the jumper pool alone, with January 27-31 as trusted context."""
    data = two_stations(FEBRUARY, {1: 420, 2: 0, 4: 0}, context=JANUARY_DUTIES[::2])
    without_south = {
        "planning_units": [unit for unit in data.planning_units if unit.planning_unit_id != SOUTH],
        "planning_unit_memberships": [row for row in data.planning_unit_memberships if row.employee_id != 4],
        "employees": [row for row in data.employees if row.employee_id != 4],
        "monthly_work_accounts": [row for row in data.monthly_work_accounts if row.employee_id != 4],
    }
    return SchedulingDataset.model_validate({**data.model_dump(round_trip=True), **without_south})
