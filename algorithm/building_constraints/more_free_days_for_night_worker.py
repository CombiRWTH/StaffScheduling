from ortools.sat.python import cp_model
import algorithm.StateManager as StateManager


def add_more_free_days_for_night_worker(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_shifts,
    num_days
) -> None:
    num_employees = len(employees)
    work = {}
    for n in range(num_employees):
        for d in range(num_days):
            work[(n, d)] = model.NewBoolVar(f'work_n{n}_d{d}')
            model.AddMaxEquality(work[(n, d)], [shifts[(n, d, s)] for s in range(num_shifts)])
    objective_terms = []
    for n in range(num_employees):
        # calculate the night shift times
        night_shifts = [shifts[(n, d, 2)] for d in range(num_days)]
        num_night_shifts = model.NewIntVar(0, num_days, f'night_count_n{n}')
        model.Add(num_night_shifts == sum(night_shifts))

        rest_days = [work[(n, d)].Not() for d in range(num_days)]
        num_rest_days = model.NewIntVar(0, num_days, f'rest_count_n{n}')
        model.Add(num_rest_days == sum(rest_days))

        surplus = model.NewIntVar(-num_days, num_days, f'rest_surplus_n{n}')
        model.Add(surplus == num_rest_days - num_night_shifts)
        objective_terms.append(surplus)

    model.Maximize(sum(objective_terms))
    StateManager.state.constraints.append("more free days for night worker")

