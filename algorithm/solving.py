from ortools.sat.python import cp_model
from handlers import UnifiedSolutionHandler
from building_constraints.initial_constraints import (
    create_shift_variables,
    add_basic_constraints,
    load_employees,
)
from building_constraints.free_shifts_and_vacation_days import (
    load_free_shifts_and_vacation_days,
    add_free_shifts_and_vacation_days,
)
from building_constraints.minimal_number_of_staff import (
    load_min_number_of_staff,
    add_min_number_of_staff,
)
import argparse
import calendar
from datetime import date, timedelta


def solve_cp_problem(
    model: cp_model.CpModel, handler: cp_model.CpSolverSolutionCallback
) -> None:
    """Solve CP model and output basic statistics."""
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.linearization_level = 0

    solver.SolveWithSolutionCallback(model, handler)

    print("\nStatistics")
    print(f"  - Conflicts     : {solver.num_conflicts}")
    print(f"  - Branches      : {solver.num_branches}")
    print(f"  - Wall time     : {solver.wall_time:.2f}s")
    print(f"  - Solutions found: {handler.solution_count() if handler else 0}")


def add_all_constraints(
    model: cp_model.CpModel,
    shifts: dict[tuple, cp_model.IntVar],
    employees: list[dict],
    case_id: int,
    num_days: int,
    num_shifts: int,
    first_weekday_of_month: int,
) -> None:
    """
    Adds constraints to the scheduling model.

    Includes:
    - Basic constraints
    - Free shifts and vacation day constraints
    - Minimal Number of Staff

    Additional constraint modules can be easily added to this function to
    extend the model.

    Args:
        model (cp_model.CpModel): The constraint programming model.
        shifts (dict[tuple, cp_model.IntVar]): Shift assignment variables.
        employees (list[dict]): List of employee data.
        case_id (int): Scheduling case ID.
        num_days (int): Number of days.
        num_shifts (int): Number of shifts per day.
        first_weekday_of_month (int): Starting day of a month, 0 for monday,
        6 for sunday.

    Returns:
        None
    """

    # Initial Constraints
    add_basic_constraints(model, employees, shifts, num_days, num_shifts)

    # Free Shifts and Vacation Days
    free_shifts_and_vacation_days = load_free_shifts_and_vacation_days(
        f"./cases/{case_id}/free_shifts_and_vacation_days.json"
    )
    add_free_shifts_and_vacation_days(
        model,
        employees,
        shifts,
        free_shifts_and_vacation_days,
        num_shifts,
    )

    min_number_of_staff = load_min_number_of_staff(
        f"./cases/{case_id}/minimal_number_of_staff.json",
    )
    add_min_number_of_staff(
        model, employees, shifts, min_number_of_staff, first_weekday_of_month, num_days
    )


def main():
    parser = argparse.ArgumentParser(
        description="Staff scheduling for a given month and year."
    )
    parser.add_argument(
        "--case_id", "-c", type=int, default=1, help="ID of the cases folder to load"
    )
    parser.add_argument(
        "--month",
        "-m",
        type=int,
        choices=range(1, 13),
        default=11,
        help="Month to plan (1-12), default: November",
    )
    parser.add_argument(
        "--year", "-y", type=int, default=2025, help="Year to plan, default: 2025"
    )
    parser.add_argument(
        "--output",
        "-o",
        nargs="+",
        default=["json"],
        help="Output formats (e.g. json, plot, print)",
    )
    args = parser.parse_args()

    # Scheduling parameters based on month and year
    SOLUTION_DIR = "found_solutions"

    CASE_ID = args.case_id
    NUM_SHIFTS = 3
    SOLUTION_LIMIT = 10
    OUTPUT = args.output

    year = args.year
    month = args.month
    # First day of the given month
    start_date = date(year, month, 1)
    # Number of days in that month
    NUM_DAYS = calendar.monthrange(year, month)[1]
    first_weekday_idx_of_month = start_date.weekday()  # 0 for Monday, 6 for Sunday

    # Generate list of dates for planning horizon
    dates = [start_date + timedelta(days=i) for i in range(NUM_DAYS)]

    model = cp_model.CpModel()
    employees = load_employees(f"./cases/{CASE_ID}/employees.json")
    shifts = create_shift_variables(model, employees, NUM_DAYS, NUM_SHIFTS)

    add_all_constraints(
        model=model,
        shifts=shifts,
        employees=employees,
        case_id=CASE_ID,
        num_days=NUM_DAYS,
        num_shifts=NUM_SHIFTS,
        first_weekday_of_month=first_weekday_idx_of_month,
    )

    unified = UnifiedSolutionHandler(
        shifts=shifts,
        employees=employees,
        num_days=NUM_DAYS,
        num_shifts=NUM_SHIFTS,
        dates=dates,
        limit=SOLUTION_LIMIT,
        case_id=CASE_ID,
        solution_dir=SOLUTION_DIR,
    )
    solve_cp_problem(model, handler=unified)

    # Output
    if "json" in OUTPUT:
        unified.json()
    if "print" in OUTPUT:
        unified.print()
    if "plot" in OUTPUT:
        unified.plot()


if __name__ == "__main__":
    main()
