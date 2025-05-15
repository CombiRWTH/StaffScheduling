import StateManager
import argparse
import calendar
from datetime import date, timedelta
from ortools.sat.python import cp_model
from handlers import UnifiedSolutionHandler
from building_constraints.initial_constraints import (
    create_shift_variables,
    create_work_on_days_variables,
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
from building_constraints.minimize_number_of_consecutive_night_shifts import (
    add_minimize_number_of_consecutive_night_shifts,
)
from building_constraints.day_no_shift_after_night_shift import (
    add_day_no_shift_after_night_shift,
)
from building_constraints.free_days_near_weekend import add_free_days_near_weekend
from building_constraints.more_free_days_for_night_worker import (
    add_more_free_days_for_night_worker,
)
from building_constraints.not_too_many_consecutive_shifts import (
    add_not_too_many_consecutive_shifts,
)
from building_constraints.shift_rotate_forward import add_shift_rotate_forward


def solve_cp_problem(
    model: cp_model.CpModel,
    handler: cp_model.CpSolverSolutionCallback,
    enumerate_all_solutions: bool,
) -> None:
    """Solve CP model and output basic statistics."""
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = (
        enumerate_all_solutions  # overwrites objective function if true
    )
    solver.parameters.linearization_level = 0

    solver.SolveWithSolutionCallback(model, handler)

    print("\nStatistics")
    print(f"  - Conflicts     : {solver.num_conflicts}")
    print(f"  - Branches      : {solver.num_branches}")
    print(f"  - Wall time     : {solver.wall_time:.2f}s")
    print(f"  - Solutions found: {handler.solution_count() if handler else 0}")


def add_objective_function(model: cp_model.CpModel, weights: dict):
    objective_terms = StateManager.state.objectives
    weighted_objective_terms = []

    # Assuming each module appends a tuple: (penalty_var, 'constraint_name')
    for penalty_var, constraint_name in objective_terms:
        if constraint_name in weights:
            weight = weights[constraint_name]
        else:
            raise KeyError(f"The weight of `{constraint_name}` is missing.")
        weighted_objective_terms.append(weight * penalty_var)

    model.Minimize(sum(weighted_objective_terms))


def add_all_constraints(
    model: cp_model.CpModel,
    shifts: dict[tuple, cp_model.IntVar],
    work_on_day: dict[tuple, cp_model.IntVar],
    employees: list[dict],
    case_id: int,
    num_days: int,
    num_shifts: int,
    first_weekday_of_month: int,
    max_consecutive_work_days: int,
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
        work_on_day (dict[tuple, cp_model.IntVar]): Whether employees work
            any shift at specific day or not
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

    # Minimize number of consevutive night shifts
    add_minimize_number_of_consecutive_night_shifts(model, employees, shifts, num_days)

    # Day no shift after night shift
    add_day_no_shift_after_night_shift(model, employees, shifts, num_days)

    # Free day near weekend
    # here we need the date of the first day in the month, need to connect with the database
    add_free_days_near_weekend(
        model, employees, work_on_day, num_days, start_weekday=first_weekday_of_month
    )

    # # More free days for night worker
    add_more_free_days_for_night_worker(model, employees, shifts, work_on_day, num_days)

    # Not to many consecutive shifts
    add_not_too_many_consecutive_shifts(
        model, employees, work_on_day, num_days, max_consecutive_work_days
    )

    # Shift rotate forward
    # fixed_shift_workers = load_shift_rotate_forward(
    #     f"./cases/{case_id}/fixed_shift_workers.json"
    # )
    add_shift_rotate_forward(model, employees, shifts, num_days)


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

    NUM_SHIFTS = 3
    SOLUTION_LIMIT = 10
    MAX_CONSECUTIVE_WORK_DAYS = 5
    OUTPUT = args.output

    # Generate list of dates for planning horizon
    dates = [start_date + timedelta(days=i) for i in range(NUM_DAYS)]

    model = cp_model.CpModel()
    employees = load_employees(f"./cases/{CASE_ID}/employees.json")
    shifts = create_shift_variables(model, employees, NUM_DAYS, NUM_SHIFTS)
    work_on_day = create_work_on_days_variables(
        model, employees, NUM_DAYS, NUM_SHIFTS, shifts
    )  # whether employee works any shift at specific day

    add_all_constraints(
        model=model,
        shifts=shifts,
        work_on_day=work_on_day,
        employees=employees,
        case_id=CASE_ID,
        num_days=NUM_DAYS,
        num_shifts=NUM_SHIFTS,
        first_weekday_of_month=first_weekday_idx_of_month,
        max_consecutive_work_days=MAX_CONSECUTIVE_WORK_DAYS,
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

    if len(StateManager.state.objectives) != 0:
        weights = {
            "Shifts rotate fowards": 1,
            "Not to long shifts": 1,
            "Minimize number of consecutive night shifts": 1,
            "free day near weekend": 1,
            "More Free Days for Night Workers": 1,
            "Not too many Consecutive Shifts": 1,
        }
        add_objective_function(model, weights)

        enumerate_all_solutions = False
    else:
        print("No objective function.")
        enumerate_all_solutions = True

    solve_cp_problem(
        model,
        handler=unified,
        enumerate_all_solutions=enumerate_all_solutions,
    )

    # Output
    if "json" in OUTPUT:
        unified.json()
    if "print" in OUTPUT:
        unified.print()
    if "plot" in OUTPUT:
        unified.plot()


if __name__ == "__main__":
    main()
