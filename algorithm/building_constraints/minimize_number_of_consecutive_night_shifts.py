from ortools.sat.python import cp_model
import StateManager


def add_minimize_number_of_consecutive_night_shifts(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_days
) -> None:
    num_employees = len(employees)
    consecutive_night_shifts = []

    for n in range(num_employees):
        for d in range(num_days - 2):  # up to second-last day
            night_today = shifts[(n, d, 2)]
            night_after_tomorrow = shifts[(n, d + 2, 2)]

            # Define a Boolean variable that is 1 if both days are night shifts
            consecutive = model.NewBoolVar(f'consec_night_n{n}_d{d}')
            model.AddBoolAnd([night_today, night_after_tomorrow]).OnlyEnforceIf(consecutive)
            model.AddBoolOr([night_today.Not(), night_after_tomorrow.Not()]).OnlyEnforceIf(consecutive.Not())

            consecutive_night_shifts.append(consecutive)

    model.Minimize(sum(consecutive_night_shifts))
    StateManager.state.constraints.append("Minimize number of cnosecutive night shifts")