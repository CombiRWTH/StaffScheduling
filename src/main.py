from __future__ import annotations

import argparse
from datetime import date, datetime

from scheduling.domain import PlanningMonth
from scheduling.logging import configure_logging
from scheduling.settings import get_settings
from scheduling.solver.cp_sat.builder import create_cp_sat_model_builder
from scheduling.solver.service import SolverService
from scheduling.timeoffice.database import create_db_engine
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.reading.container import TimeOfficeReaders
from scheduling.timeoffice.service import TimeOfficeService
from scheduling.timeoffice.writing.solution import TimeOfficeSolutionWriter


def _parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(f"Invalid date '{value}'. Use YYYY-MM-DD or DD.MM.YYYY.")


def _solve(
    unit: int,
    start_date: date,
    end_date: date,
) -> None:
    planning_month = PlanningMonth(year=start_date.year, month=start_date.month)

    if start_date != planning_month.start or end_date != planning_month.end:
        raise SystemExit(
            "The new solver works on full planning months. "
            f"Use {planning_month.start.isoformat()} through {planning_month.end.isoformat()}."
        )

    settings = get_settings()
    configure_logging(level=settings.log_level)

    engine = create_db_engine(settings=settings)
    facts = TIMEOFFICE_FACTS
    timeoffice = TimeOfficeService(
        facts=facts,
        engine=engine,
        readers=TimeOfficeReaders.create(facts=facts),
        solution_writer=TimeOfficeSolutionWriter(),
    )
    solver = SolverService(
        settings=settings,
        model_builder=create_cp_sat_model_builder(),
    )

    print(f"Creating staff schedule for planning unit {unit}...")

    try:
        dataset = timeoffice.fetch_dataset(
            planning_unit_ids=(unit,),
            planning_month=planning_month,
        )
        solution = solver.solve(dataset)
        solution_name = f"solution_{unit}_{start_date}-{end_date}_wdefault"
        legacy_solution_paths = timeoffice.write_solution_legacy_format(
            dataset=dataset,
            solution=solution,
            solution_name=solution_name,
        )
    except ValueError as e:
        raise SystemExit(str(e)) from None
    finally:
        engine.dispose()

    if legacy_solution_paths is not None:
        print(f"Saved legacy solution: {legacy_solution_paths.solution_path}")
        print(f"Saved processed legacy solution: {legacy_solution_paths.processed_solution_path}")

    print(
        "Solved staff schedule: "
        f"status={solution.status.value}, generated_assignments={len(solution.assignments)}, "
        f"diagnostics={len(solution.diagnostics)}, audit_findings={len(solution.audit.findings)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="staff-scheduling")
    subparsers = parser.add_subparsers(dest="command", required=True)

    solve_parser = subparsers.add_parser("solve", help="Solve the scheduling problem for a planning unit")
    solve_parser.add_argument("unit", type=int)
    solve_parser.add_argument("start", type=_parse_date)
    solve_parser.add_argument("end", type=_parse_date)

    args = parser.parse_args()

    if args.command == "solve":
        _solve(args.unit, args.start, args.end)


if __name__ == "__main__":
    main()
