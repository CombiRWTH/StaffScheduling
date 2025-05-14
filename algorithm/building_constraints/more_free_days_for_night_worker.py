from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "More Free Days for Night Workers"


def add_more_free_days_for_night_worker(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    work_on_day: dict[tuple, cp_model.IntVar],
    num_days: int,
) -> None:
    num_employees = len(employees)
    objective_terms = []
    for n in range(num_employees):
        # calculate the night shift times
        night_shifts = [shifts[(n, d_idx, 2)] for d_idx in range(num_days)]
        num_night_shifts = model.NewIntVar(0, num_days, f"night_count_n{n}")
        model.Add(num_night_shifts == sum(night_shifts))

        rest_days = [work_on_day[(n, d_idx)].Not() for d_idx in range(num_days)]
        num_rest_days = model.NewIntVar(0, num_days, f"rest_count_n{n}")
        model.Add(num_rest_days == sum(rest_days))

        surplus = model.NewIntVar(-num_days, num_days, f"rest_surplus_n{n}")
        model.Add(surplus == num_rest_days - num_night_shifts)
        objective_terms.append(surplus)

    # Maximize sum(objective_terms)

    StateManager.state.objectives.append((-sum(objective_terms), NAME_OF_CONSTRAINT))
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
