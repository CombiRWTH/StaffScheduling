"""Solve, validate and describe portable monthly bundles without TimeOffice.

    python -m app.solver.examples solve FOLDER [--timeout SECONDS]
    python -m app.solver.examples check DIRECTORY --first YYYY-MM --last YYYY-MM
    python -m app.solver.examples schema DIRECTORY

`solve` reads FOLDER/input.json and writes result.json, schedule.csv and employees.csv beside it.
`check` accepts the monthly folders FIRST to LAST as hand-in examples only if every folder is a complete,
accepted bundle and consecutive months agree on their shared context. `schema` writes the JSON Schemas
of input.json and result.json.
"""

import argparse
import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel

from app.domain import CheckStatus, PlanningMonth
from app.settings import get_settings
from app.solver.bundle import (
    EMPLOYEES_FILE,
    FILES,
    INPUT_FILE,
    RESULT_FILE,
    SCHEDULE_FILE,
    BundleProblem,
    InvalidBundle,
    ScheduleBundle,
    ScheduleInput,
    ScheduleResult,
    read_input,
)
from app.solver.service import SolverService


@dataclass
class Report:
    summaries: list[str] = field(default_factory=list[str])
    problems: list[str] = field(default_factory=list[str])


def solve_folder(folder: Path, timeout: float | None) -> str:
    """Solve FOLDER/input.json and write the other three files; raises InvalidBundle without a schedule."""
    input_json = (folder / INPUT_FILE).read_bytes()
    solution = SolverService(get_settings()).solve(read_input(input_json).dataset, timeout)
    if not solution.found:
        reasons = "; ".join(row.message for row in solution.diagnostics)
        raise InvalidBundle(BundleProblem.NO_SCHEDULE, f"no schedule ({solution.status.value}). {reasons}")
    bundle = ScheduleBundle.solved(input_json, solution)
    for name in (RESULT_FILE, SCHEDULE_FILE, EMPLOYEES_FILE):
        (folder / name).write_bytes(bundle.files[name])
    return _summary(folder.name, bundle)


def check_examples(directory: Path, first: PlanningMonth, last: PlanningMonth) -> Report:
    """Validate the monthly folders `first` to `last` of DIRECTORY and their sequence."""
    report = Report()
    months = _months(first, last)
    labels = {_label(month) for month in months}
    if extra := sorted(path.name for path in directory.glob("????-??") if path.name not in labels):
        report.problems.append(f"Folders outside {_label(first)} to {_label(last)}: {', '.join(extra)}.")
    bundles: list[ScheduleBundle | None] = [_check_folder(directory / _label(month), month, report) for month in months]
    loaded = [bundle for bundle in bundles if bundle is not None]
    if any(bundle.input.dataset.planning_units != loaded[0].input.dataset.planning_units for bundle in loaded):
        report.problems.append("The months do not plan the same stations and jumper pools.")
    for earlier, later in zip(bundles, bundles[1:], strict=False):
        if earlier is not None and later is not None:
            report.problems.extend(_sequence_problems(earlier, later))
    return report


def write_schemas(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, model in (("input.schema.json", ScheduleInput), ("result.schema.json", ScheduleResult)):
        (directory / name).write_text(json.dumps(model.model_json_schema(), indent=2, ensure_ascii=False) + "\n")


def _check_folder(folder: Path, month: PlanningMonth, report: Report) -> ScheduleBundle | None:
    label = folder.name
    if missing := [name for name in FILES if not (folder / name).is_file() or not (folder / name).stat().st_size]:
        report.problems.append(f"{label}: missing or empty {', '.join(missing)}.")
        return None
    try:
        bundle = ScheduleBundle.read((folder / INPUT_FILE).read_bytes(), (folder / RESULT_FILE).read_bytes())
    except InvalidBundle as error:
        report.problems.append(f"{label}: {error}")
        return None
    if bundle.input.dataset.planning_month != month:
        report.problems.append(f"{label}: the bundle plans another month.")
    for name in (RESULT_FILE, SCHEDULE_FILE, EMPLOYEES_FILE):
        if (folder / name).read_bytes() != bundle.files[name]:
            report.problems.append(f"{label}: {name} differs from the canonical rendering of the pair.")
    check = bundle.check
    if check.status != CheckStatus.ACCEPTED:
        blocking = sorted({row.rule.value for row in check.not_assessed if row.blocking})
        report.problems.append(
            f"{label}: diagnostic result, not an example: schedule check {check.status.value} with "
            f"{len(check.findings)} findings and blocking gaps in {blocking or 'no rule'}."
        )
    if any(row.origin_unit_id is None for row in bundle.tables.duties):
        report.problems.append(f"{label}: a duty has no evidenced origin.")
    report.summaries.append(_summary(label, bundle))
    return bundle


def _sequence_problems(earlier: ScheduleBundle, later: ScheduleBundle) -> list[str]:
    """Each month's context duties on the other month's dates must be that month's schedule."""
    problems: list[str] = []
    label = f"{_label(earlier.input.dataset.planning_month)} to {_label(later.input.dataset.planning_month)}"
    for context, schedule in ((later, earlier), (earlier, later)):
        reader, month = context.input.dataset, schedule.input.dataset.planning_month
        employees = {row.employee_id for row in reader.employees}
        days = {day for day in month.dates if reader.context.covers(day)}
        trusted = _rows(row for row in reader.context.duties if row.date in days)
        scheduled = _rows(
            row for row in schedule.result.solution.assignments if row.date in days and row.employee_id in employees
        )
        if trusted != scheduled:
            problems.append(f"{label}: the context duties on {_label(month)} dates differ from its schedule.")
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


def _summary(label: str, bundle: ScheduleBundle) -> str:
    solution, check = bundle.result.solution, bundle.check
    stations = ", ".join(sorted({row.planning_unit_name for row in bundle.tables.duties}))
    open_rules = sorted({row.rule.value for row in check.not_assessed})
    return (
        f"{label}: {solution.status.value}, check {check.status.value}, {len(bundle.tables.duties)} duties "
        f"at {stations or 'no station'}, {len(bundle.tables.employees)} employees; not assessed: "
        f"{', '.join(open_rules) or 'nothing'}."
    )


def _months(first: PlanningMonth, last: PlanningMonth) -> list[PlanningMonth]:
    months = [first]
    while (months[-1].year, months[-1].month) < (last.year, last.month):
        year, month = divmod(months[-1].year * 12 + months[-1].month, 12)
        months.append(PlanningMonth(year=year, month=month + 1))
    return months


def _label(month: PlanningMonth) -> str:
    return f"{month.year}-{month.month:02d}"


def _month(text: str) -> PlanningMonth:
    year, month = text.split("-")
    return PlanningMonth(year=int(year), month=int(month))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.solver.examples", description="Solve, validate and describe portable monthly bundles."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    solve = commands.add_parser("solve", help="solve FOLDER/input.json and write the other files")
    solve.add_argument("folder", type=Path)
    solve.add_argument("--timeout", type=float, help="solver seconds; default SOLVER_MAX_TIME_SECONDS")
    check = commands.add_parser("check", help="validate the monthly folders FIRST to LAST")
    check.add_argument("directory", type=Path)
    check.add_argument("--first", type=_month, required=True, help="YYYY-MM")
    check.add_argument("--last", type=_month, required=True, help="YYYY-MM")
    schema = commands.add_parser("schema", help="write the JSON Schemas of input.json and result.json")
    schema.add_argument("directory", type=Path)
    args = parser.parse_args(argv)

    if args.command == "solve":
        try:
            print(solve_folder(args.folder, args.timeout))
        except InvalidBundle as error:
            print(f"{args.folder.name}: {error}", file=sys.stderr)
            return 1
        return 0
    if args.command == "check":
        report = check_examples(args.directory, args.first, args.last)
        print("\n".join(report.summaries))
        for problem in report.problems:
            print(f"FAIL {problem}", file=sys.stderr)
        print("FAIL" if report.problems else "PASS", f"{len(report.problems)} problems")
        return 1 if report.problems else 0
    write_schemas(args.directory)
    return 0


if __name__ == "__main__":
    sys.exit(main())
