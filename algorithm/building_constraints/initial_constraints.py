import json
import StateManager
from ortools.sat.python import cp_model


def load_general_settings(filename):
    with open(filename, "r") as f:
        config = json.load(f)
    return config


def load_employees(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data["employees"]


def create_shift_variables(
    model: cp_model.CpModel, employees: list[dict], num_days: int, num_shifts: int
) -> dict[tuple, cp_model.IntVar]:
    """
    Creates shift assignment variables for each employee, day, and shift.
    """
    shifts = {}
    for n_idx, employee in enumerate(employees):
        for d in range(num_days):
            for s in range(num_shifts):
                shifts[(n_idx, d + 1, s)] = model.new_bool_var(
                    f"shift_{employee['name']}_d{d}_s{s}"
                )
    return shifts


def add_basic_constraints(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_days: int,
    num_shifts: int,
) -> None:
    """
    Adds fundamental scheduling constraints:

    - Each shift on each day is assigned to exactly one employee.
    - Each employee can work at most one shift per day.

    These constraints form the structural foundation of the schedule.
    """

    num_employees = len(employees)
    all_employees = range(num_employees)
    all_shifts = range(num_shifts)
    all_days = range(num_days)

    # one shift per employee per day at most
    for n in all_employees:
        for d in all_days:
            model.add_at_most_one(shifts[(n, d + 1, s)] for s in all_shifts)

    StateManager.state.constraints.append("Initial")
