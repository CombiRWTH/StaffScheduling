from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "24h no shift after night shift phase"


def add_day_no_shift_after_night_shift(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_days,
) -> None:
    num_employees = len(employees)

    for n in range(num_employees):
        for d in range(num_days - 1):  # up to second-last day
            night_today = shifts[(n, d, 2)]
            not_night_tomorrow = shifts[(n, d + 1, 2)].Not()

            # include Z (index 3) if it exists in this model
            tomorrow_terms = [
                shifts[(n, d + 1, s)] for s in (0, 1, 2, 3) if (n, d + 1, s) in shifts
            ]
            shift_tomorrow = sum(tomorrow_terms)

            model.Add(shift_tomorrow == 0).OnlyEnforceIf(
                [night_today, not_night_tomorrow]
            )

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
