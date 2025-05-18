import StateManager
from ortools.sat.python import cp_model

NAME_OF_CONSTRAINT = "Inital Constraints"


def create_shift_variables(
    model: cp_model.CpModel, employees: list[dict], num_days: int, num_shifts: int
) -> dict[tuple, cp_model.IntVar]:
    """
    Creates shift assignment variables for each employee, day, and shift.
    """
    shifts = {}
    for n_idx, employee in enumerate(employees):
        for d_idx in range(num_days):
            for s in range(num_shifts):
                shifts[(n_idx, d_idx, s)] = model.new_bool_var(
                    f"shift_{employee['name']}_d{d_idx}_s{s}"
                )
    return shifts


def create_work_on_days_variables(
    model: cp_model.CpModel,
    employees: list[dict],
    num_days: int,
    num_shifts: int,
    shifts: dict[str, cp_model.IntVar],
) -> dict[tuple, cp_model.IntVar]:
    """
    Creates workday variables for each employee, each day. If 1, the employee
    has to work that day (any shift), if 0, they do not work any shift that day.
    """
    work_on_day = {}
    for n_idx, employee in enumerate(employees):
        for d_idx in range(num_days):
            work_on_day[(n_idx, d_idx)] = model.NewBoolVar(
                f"work_{employee['name']}_d{d_idx}"
            )
            model.AddMaxEquality(
                work_on_day[(n_idx, d_idx)],
                [shifts[(n_idx, d_idx, s)] for s in range(num_shifts)],
            )
    return work_on_day


def add_basic_constraints(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_days: int,
    num_shifts: int,
) -> None:
    """
    Adds fundamental scheduling constraints:

    - Each employee can work at most one shift per day.

    These constraints form the structural foundation of the schedule.
    """

    num_employees = len(employees)
    all_employees = range(num_employees)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    # one shift per employee per day at most
    for n in all_employees:
        for d_idx in all_days:
            model.add_at_most_one(shifts[(n, d_idx, s)] for s in all_shifts)

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
