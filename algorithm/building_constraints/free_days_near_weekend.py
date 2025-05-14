from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "free day near weekend"


def add_free_days_near_weekend(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_shifts,
    num_days,
) -> None:
    # here we assume that the start of the month is Friday, but we need further adjust
    start_weekday = 4
    num_employees = len(employees)
    work = {}
    for n in range(num_employees):
        for d in range(num_days):
            work[(n, d)] = model.NewBoolVar(f"work_n{n}_d{d}")
            model.AddMaxEquality(
                work[(n, d)], [shifts[(n, d, s)] for s in range(num_shifts)]
            )

    objective_terms = []

    for n in range(num_employees):
        for d in range(num_days - 1):
            # consecutive two day rest
            rest_pair = model.NewBoolVar(f"rest_pair_n{n}_d{d}")
            model.Add(work[(n, d)] == 0).OnlyEnforceIf(rest_pair)
            model.Add(work[(n, d + 1)] == 0).OnlyEnforceIf(rest_pair)
            model.Add(work[(n, d)] + work[(n, d + 1)] != 0).OnlyEnforceIf(
                rest_pair.Not()
            )
            objective_terms.append(rest_pair)

        for d in range(1, num_days - 1):
            # isolated single-day rest penalty (working before and after)
            solo_rest = model.NewBoolVar(f"solo_rest_n{n}_d{d}")
            model.Add(work[(n, d - 1)] == 1).OnlyEnforceIf(solo_rest)
            model.Add(work[(n, d)] == 0).OnlyEnforceIf(solo_rest)
            model.Add(work[(n, d + 1)] == 1).OnlyEnforceIf(solo_rest)
            model.Add(
                sum([work[(n, d - 1)], work[(n, d)], work[(n, d + 1)]]) == 2
            ).OnlyEnforceIf(solo_rest)
            model.Add(
                sum([work[(n, d - 1)], work[(n, d)], work[(n, d + 1)]]) != 2
            ).OnlyEnforceIf(solo_rest.Not())
            objective_terms.append(
                -solo_rest
            )  # Extra points when there is no isolation

        for d in range(num_days):
            # weekend off incentive
            weekday = (start_weekday + d) % 7
            if weekday in [5, 6]:  # Saturday and Sunday
                rest_weekend = model.NewBoolVar(f"rest_weekend_n{n}_d{d}")
                model.Add(work[(n, d)] == 0).OnlyEnforceIf(rest_weekend)
                model.Add(work[(n, d)] == 1).OnlyEnforceIf(rest_weekend.Not())
                objective_terms.append(rest_weekend)
        # Maximize sum(objective_terms)

        StateManager.state.objectives.append(
            (-sum(objective_terms), NAME_OF_CONSTRAINT)
        )
        StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
