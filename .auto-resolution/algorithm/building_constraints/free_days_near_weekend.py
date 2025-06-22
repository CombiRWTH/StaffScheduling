from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "free day near weekend"


# def add_free_days_near_weekend(
#     model: cp_model.CpModel,
#     employees: list[dict],
#     work_on_day: dict[tuple, cp_model.IntVar],
#     num_days,
#     start_weekday,
# ) -> None:
#     weights = {
#         "consecutive_2_days_rest": 1,
#         "single-day rest penalty": 1,
#         "rest_weekend": 1,
#     }
#
#     num_employees = len(employees)
#     objective_terms = []
#
#     for n in range(num_employees):
#         for d in range(num_days - 1):
#             # consecutive two day rest
#             rest_pair = model.NewBoolVar(f"rest_pair_n{n}_d{d}")
#             model.Add(work_on_day[(n, d)] == 0).OnlyEnforceIf(rest_pair)
#             model.Add(work_on_day[(n, d + 1)] == 0).OnlyEnforceIf(rest_pair)
#             model.Add(work_on_day[(n, d)] + work_on_day[(n, d + 1)] != 0).OnlyEnforceIf(
#                 rest_pair.Not()
#             )
#             objective_terms.append(weights["consecutive_2_days_rest"] * rest_pair)
#
#         for d in range(1, num_days - 1):
#             # isolated single-day rest penalty (working before and after)
#             solo_rest = model.NewBoolVar(f"solo_rest_n{n}_d{d}")
#             model.Add(work_on_day[(n, d - 1)] == 1).OnlyEnforceIf(solo_rest)
#             model.Add(work_on_day[(n, d)] == 0).OnlyEnforceIf(solo_rest)
#             model.Add(work_on_day[(n, d + 1)] == 1).OnlyEnforceIf(solo_rest)
#             model.Add(
#                 sum(
#                     [
#                         work_on_day[(n, d - 1)],
#                         work_on_day[(n, d)],
#                         work_on_day[(n, d + 1)],
#                     ]
#                 )
#                 == 2
#             ).OnlyEnforceIf(solo_rest)
#             model.Add(
#                 sum(
#                     [
#                         work_on_day[(n, d - 1)],
#                         work_on_day[(n, d)],
#                         work_on_day[(n, d + 1)],
#                     ]
#                 )
#                 != 2
#             ).OnlyEnforceIf(solo_rest.Not())
#             objective_terms.append(
#                 -solo_rest * weights["single-day rest penalty"]
#             )  # Extra points when there is no isolation
#
#         for d in range(num_days):
#             # weekend off incentive
#             weekday = (start_weekday + d) % 7
#             if weekday in [5, 6]:  # Saturday and Sunday
#                 rest_weekend = model.NewBoolVar(f"rest_weekend_n{n}_d{d}")
#                 model.Add(work_on_day[(n, d)] == 0).OnlyEnforceIf(rest_weekend)
#                 model.Add(work_on_day[(n, d)] == 1).OnlyEnforceIf(rest_weekend.Not())
#                 objective_terms.append(rest_weekend * weights["rest_weekend"])
#         # Maximize sum(objective_terms)
#
#         StateManager.state.objectives.append(
#             (-sum(objective_terms), NAME_OF_CONSTRAINT)
#         )
#     StateManager.state.constraints.append(NAME_OF_CONSTRAINT)


def add_free_days_near_weekend(
    model: cp_model.CpModel,
    employees: list[dict],
    work_on_day: dict[tuple, cp_model.IntVar],
    num_days,
    start_weekday,
) -> None:
    weights = {
        "consecutive_2_days_rest": 1,
        "single-day_rest_penalty": 1,
        "rest_weekend": 1,
    }

    num_employees = len(employees)
    objective_terms = []

    for n in range(num_employees):
        for d in range(num_days - 1):
            # penalty: If work on one of the two days, penalty += 1
            # Bonus for two consecutive days off
            both_rest = model.NewBoolVar(f"both_rest_n{n}_d{d}")
            model.AddBoolAnd(
                [work_on_day[(n, d)].Not(), work_on_day[(n, d + 1)].Not()]
            ).OnlyEnforceIf(both_rest)
            model.AddBoolOr(
                [work_on_day[(n, d)], work_on_day[(n, d + 1)]]
            ).OnlyEnforceIf(both_rest.Not())

            # penalty: If not rest on consecutive two days
            consecutive_rest_penalty = model.NewIntVar(
                0, 1, f"consecutive_rest_penalty_{n}_{d}"
            )
            model.Add(consecutive_rest_penalty == 1 - both_rest)
            objective_terms.append(
                consecutive_rest_penalty * weights["consecutive_2_days_rest"]
            )

        for d in range(1, num_days - 1):
            # rest on only one day penalty
            solo_rest = model.NewBoolVar(f"solo_rest_n{n}_d{d}")
            model.AddBoolAnd(
                [
                    work_on_day[(n, d - 1)],
                    work_on_day[(n, d + 1)],
                    work_on_day[(n, d)].Not(),
                ]
            ).OnlyEnforceIf(solo_rest)
            model.AddBoolOr(
                [
                    work_on_day[(n, d - 1)].Not(),
                    work_on_day[(n, d + 1)].Not(),
                    work_on_day[(n, d)],
                ]
            ).OnlyEnforceIf(solo_rest.Not())

            solo_rest_penalty = model.NewIntVar(0, 1, f"solo_rest_penalty_{n}_{d}")
            model.Add(solo_rest_penalty == solo_rest)
            objective_terms.append(
                solo_rest_penalty * weights["single-day_rest_penalty"]
            )

        for d in range(num_days):
            weekday = (start_weekday + d) % 7
            if weekday in [5, 6]:  # Saturday or Sunday
                # bonus for rest in the weekend
                rest_weekend_bonus = model.NewBoolVar(f"rest_weekend_bonus_{n}_{d}")
                model.Add(work_on_day[(n, d)] == 0).OnlyEnforceIf(rest_weekend_bonus)
                model.Add(work_on_day[(n, d)] == 1).OnlyEnforceIf(
                    rest_weekend_bonus.Not()
                )

                weekend_penalty = model.NewIntVar(0, 1, f"weekend_penalty_{n}_{d}")
                model.Add(weekend_penalty == 1 - rest_weekend_bonus)
                objective_terms.append(weekend_penalty * weights["rest_weekend"])

    # package the whole thing into a soft constraint
    StateManager.state.objectives.append((sum(objective_terms), NAME_OF_CONSTRAINT))
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
