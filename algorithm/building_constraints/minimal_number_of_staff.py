import StateManager

NAME_OF_CONSTRAINT = "Minimal Number of Staff"


def add_min_number_of_staff(
    model,
    employees,
    shifts,
    requirements,
    employee_types,
    first_weekday_idx_of_month,
    last_day_of_month,
):
    employee_idx_by_type = {}
    for idx, employee in enumerate(employees):
        employee_idx_by_type.setdefault(employee["type"], []).append(idx)

    weekday_mapping = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    shift_mapping = ["F", "S", "N"]

    for day_idx in range(0, last_day_of_month):
        current_weekday_index = (first_weekday_idx_of_month + day_idx) % len(
            weekday_mapping
        )
        current_weekday = weekday_mapping[current_weekday_index]
        for staff_type in requirements.keys():
            staff_groups = employee_types[staff_type]
            relevant_employees = [
                employee_id
                for staff_group in staff_groups
                for employee_id in employee_idx_by_type[staff_group]
            ]
            for shift in requirements[staff_type][current_weekday].keys():
                shift_index = shift_mapping.index(shift)
                required_count = requirements[staff_type][current_weekday][shift]
                work_vars = [
                    shifts[(n, day_idx, shift_index)] for n in relevant_employees
                ]
                model.Add(sum(work_vars) >= required_count)

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
