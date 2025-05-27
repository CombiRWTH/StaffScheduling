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
        for d in range(num_days - 1):  # to the last second day
            is_night_today = shifts[(n, d, 2)]
            is_night_tomorrow = shifts[(n, d + 1, 2)]

            # check if today is the last night shift in the night block
            is_end_of_night_block = model.NewBoolVar(f"end_of_night_block_n{n}_d{d}")
            model.AddBoolAnd([is_night_today, is_night_tomorrow.Not()]).OnlyEnforceIf(
                is_end_of_night_block
            )
            model.AddBoolOr([is_night_today.Not(), is_night_tomorrow]).OnlyEnforceIf(
                is_end_of_night_block.Not()
            )

            for s in range(3):
                model.Add(shifts[(n, d + 1, s)] == 0).OnlyEnforceIf(
                    is_end_of_night_block
                )

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)


# def add_day_no_shift_after_night_shift(
#     model: cp_model.CpModel,
#     employees: list[dict],
#     shifts: dict[tuple, cp_model.IntVar],
#     num_days,
# ) -> None:
#     num_employees = len(employees)
#     penalty_weight = 1
#     penalty_var_list = []
#
#     for n in range(num_employees):
#         for d in range(num_days - 1):  # Up to second-last day
#             night_today = shifts[(n, d, 2)]
#             shift_tomorrow_sum = shifts[(n, d + 1, 0)] + shifts[(n, d + 1, 1)]
#
#             shift_tomorrow_bool = model.NewBoolVar(f"has_shift_after_night_n{n}_d{d}")
#             model.Add(shift_tomorrow_sum > 0).OnlyEnforceIf(shift_tomorrow_bool)
#             model.Add(shift_tomorrow_sum == 0).OnlyEnforceIf(shift_tomorrow_bool.Not())
#
#             penalty_var = model.NewBoolVar(f"penalty_shift_after_night_n{n}_d{d}")
#
#             model.AddBoolAnd([
#                 night_today,
#                 shift_tomorrow_bool
#             ]).OnlyEnforceIf(penalty_var)
#
#             model.AddImplication(penalty_var, night_today)
#             model.AddImplication(penalty_var, shift_tomorrow_bool)
#
#             # collect penalty
#             penalty_var_list.append((penalty_var, penalty_weight))
#
#     StateManager.state.objectives.append((sum(var * weight for var, weight in penalty_var_list), NAME_OF_CONSTRAINT))
#     StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
