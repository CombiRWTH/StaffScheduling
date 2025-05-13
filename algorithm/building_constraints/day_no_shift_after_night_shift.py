from ortools.sat.python import cp_model
import StateManager


def add_day_no_shift_after_night_shift(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_days
) -> None:
    num_employees = len(employees)

    for n in range(num_employees):
        for d in range(num_days - 1):  # up to second-last day
            night_today = shifts[(n, d, 2)]
            not_night_tomorrow = shifts[(n, d + 1, 2)]
            shift_tomorrow = shifts[(n, d + 1, 0)] + shifts[(n, d + 1, 1)] + shifts[(n, d + 1, 2)]
            model.Add(shift_tomorrow == 0).OnlyEnforceIf(night_today & not_night_tomorrow)

    StateManager.state.constraints.append("day no shift after night shift")
