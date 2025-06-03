import StateManager
from ortools.sat.python import cp_model

NAME_OF_CONSTRAINT = "Minimum rest time"


def add_minimum_rest_time(
    model: cp_model.CpModel,
    employees: list[dict],
    num_days: int,
    shifts: dict[tuple, cp_model.IntVar],
) -> None:
    num_employees = len(employees)

    for n in range(num_employees):
        for d in range(num_days - 1):
            late_today = shifts[(n, d, 1)]
            not_early_tomorrow = shifts[(n, d + 1, 0)].Not()
            model.AddImplication(late_today, not_early_tomorrow)

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
