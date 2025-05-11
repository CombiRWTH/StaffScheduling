import json
import StateManager


def load_min_number_of_staff(filename):
    with open(filename, "r") as f:
        return json.load(f)


def add_min_number_of_staff(
    model, employees, shifts, requirements, first_weekday_of_month, last_day_of_month
):
    employee_idx_by_type = {}
    for idx, employee in enumerate(employees):
        employee_idx_by_type.setdefault(employee["type"], []).append(idx)

    weekday_mapping = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    shift_mapping = ["F", "S", "N"]

    if first_weekday_of_month not in weekday_mapping:
        raise ValueError("Invalid weekday provided.")
    weekday_index = weekday_mapping.index(first_weekday_of_month)
    for day in range(1, last_day_of_month + 1):
        current_weekday_index = (weekday_index + (day - 1)) % len(weekday_mapping)
        current_weekday = weekday_mapping[current_weekday_index]
        for staff_type in requirements.keys():
            relevant_employees = employee_idx_by_type[staff_type]
            for shift in requirements[staff_type][current_weekday].keys():
                shift_index = shift_mapping.index(shift)
                required_count = requirements[staff_type][current_weekday][shift]
                work_vars = [shifts[(n, day, shift_index)] for n in relevant_employees]
                model.Add(sum(work_vars) >= required_count)

    # for staff_type, days_of_week in requirements.items():
    #     relevant_employees = employee_idx_by_type[staff_type]
    #     for day, number_per_shift in days_of_week.items():
    #         for shift, required_count in number_per_shift.items():
    #             work_vars = [shifts[(n, day, shift)] for n in relevant_employees]
    #             model.Add(sum(work_vars) >= required_count)

    StateManager.state.constraints.append("Minimal Number of Staff")
