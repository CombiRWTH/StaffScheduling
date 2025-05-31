import StateManager

NAME_OF_CONSTRAINT = "Intermediate Shifts"


def add_intermediate_shifts(
    model,
    employees,
    shifts,
    first_weekday_idx_of_month,
    last_day_of_month,
):
    shift_index_for_Z = 3  # "Z"
    num_employees = len(employees)

    penalty_terms = []
    for day_idx in range(last_day_of_month):
        weekday_index = (first_weekday_idx_of_month + day_idx) % 7
        is_weekend = weekday_index in [5, 6]  # Saturday or Sunday

        z_shift_vars = []

        for emp_idx in range(num_employees):
            key = (emp_idx, day_idx, shift_index_for_Z)
            if key in shifts:
                z_shift_vars.append(shifts[key])

        # Hard constraint: max 2 Z shifts per day
        if z_shift_vars:
            total_z = model.NewIntVar(0, num_employees, f"total_z_day{day_idx}")
            model.Add(total_z == sum(z_shift_vars))
            model.Add(total_z <= 2)

            # Use auxiliary vars to model penalty tiers
            is_second_z = model.NewBoolVar(f"is_second_z_day{day_idx}")
            model.Add(total_z >= 2).OnlyEnforceIf(is_second_z)
            model.Add(total_z < 2).OnlyEnforceIf(is_second_z.Not())

            is_any_z = model.NewBoolVar(f"is_any_z_day{day_idx}")
            model.Add(total_z >= 1).OnlyEnforceIf(is_any_z)
            model.Add(total_z < 1).OnlyEnforceIf(is_any_z.Not())

            if is_weekend:
                # 1st Z on weekend = +10
                # 2nd Z on weekend = +100
                penalty_terms.append((is_any_z, 10))
                penalty_terms.append((is_second_z, 90))  # cumulative +100
            else:
                # 2nd Z on weekday = +20
                penalty_terms.append((is_second_z, 20))

    # StateManager.state.objectives.append((sum(var * weight for var, weight in penalty_terms), NAME_OF_CONSTRAINT))
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
