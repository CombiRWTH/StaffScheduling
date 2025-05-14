from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "free day near weekend"


def add_free_days_near_weekend(
    model: cp_model.CpModel,
    employees: list[dict],
    work_on_day: dict[tuple, cp_model.IntVar],
    num_days,
    start_weekday,
) -> None:
    weights = {
        "consecutive_2_days_rest": 1,
        "single-day rest penalty": 1,
        "rest_weekend": 1,
    }

    num_employees = len(employees)
    objective_terms = []

    for n in range(num_employees):
        for d in range(num_days - 1):
            # consecutive two day rest
            rest_pair = model.NewBoolVar(f"rest_pair_n{n}_d{d}")
            model.Add(work_on_day[(n, d)] == 0).OnlyEnforceIf(rest_pair)
            model.Add(work_on_day[(n, d + 1)] == 0).OnlyEnforceIf(rest_pair)
            model.Add(work_on_day[(n, d)] + work_on_day[(n, d + 1)] != 0).OnlyEnforceIf(
                rest_pair.Not()
            )
            objective_terms.append(weights["consecutive_2_days_rest"] * rest_pair)

        for d in range(1, num_days - 1):
            # isolated single-day rest penalty (working before and after)
            solo_rest = model.NewBoolVar(f"solo_rest_n{n}_d{d}")
            model.Add(work_on_day[(n, d - 1)] == 1).OnlyEnforceIf(solo_rest)
            model.Add(work_on_day[(n, d)] == 0).OnlyEnforceIf(solo_rest)
            model.Add(work_on_day[(n, d + 1)] == 1).OnlyEnforceIf(solo_rest)
            model.Add(
                sum(
                    [
                        work_on_day[(n, d - 1)],
                        work_on_day[(n, d)],
                        work_on_day[(n, d + 1)],
                    ]
                )
                == 2
            ).OnlyEnforceIf(solo_rest)
            model.Add(
                sum(
                    [
                        work_on_day[(n, d - 1)],
                        work_on_day[(n, d)],
                        work_on_day[(n, d + 1)],
                    ]
                )
                != 2
            ).OnlyEnforceIf(solo_rest.Not())
            objective_terms.append(
                -solo_rest * weights["single-day rest penalty"]
            )  # Extra points when there is no isolation

        for d in range(num_days):
            # weekend off incentive
            weekday = (start_weekday + d) % 7
            if weekday in [5, 6]:  # Saturday and Sunday
                rest_weekend = model.NewBoolVar(f"rest_weekend_n{n}_d{d}")
                model.Add(work_on_day[(n, d)] == 0).OnlyEnforceIf(rest_weekend)
                model.Add(work_on_day[(n, d)] == 1).OnlyEnforceIf(rest_weekend.Not())
                objective_terms.append(rest_weekend * weights["rest_weekend"])
        # Maximize sum(objective_terms)

        StateManager.state.objectives.append(
            (-sum(objective_terms), NAME_OF_CONSTRAINT)
        )
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
