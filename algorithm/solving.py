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
    first_weekday_of_month: str,
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
        first_weekday_of_month (str): Starting day of a month, e.g. 'Di' for
        Tuesday.

    Returns:
        None
    """

    # Inital Constraints
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
        f"./cases/{case_id}/minimal_number_of_staff copy.json",
    )
    print(min_number_of_staff)
    add_min_number_of_staff(
        model, employees, shifts, min_number_of_staff, first_weekday_of_month, num_days
    )


def main():
    SOLUTION_DIR = "found_solutions"
    CASE_ID = 1
    NUM_DAYS = 30
    FIRST_WEEKDAY_OF_MONTH = "Mo"
    NUM_SHIFTS = 3
    SOLUTION_LIMIT = 10
    OUTPUT = ["json"]

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
        first_weekday_of_month=FIRST_WEEKDAY_OF_MONTH,
    )

    # Solving
    unified = UnifiedSolutionHandler(
        shifts=shifts,
        employees=employees,
        num_days=NUM_DAYS,
        num_shifts=NUM_SHIFTS,
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
