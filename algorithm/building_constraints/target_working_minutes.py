import StateManager

NAME_OF_CONSTRAINT = "Target Working minutes"


# Idee: Einbau erstmal nur von Obergrenze
# Dann wenn zu noch Stunden übrig, Zwischendienst auffüllen
# ist ein ein Problem VIELE zwischendienste aufzufüllen und dann später manuell aufzuteilen


def add_target_working_minutes(
    model, employees, shifts, num_days, num_shifts, target_min_data
):
    """
    Adds a constraint to the model that ensures each employee's total working time
    is within [target_minutes - tolerance_less, target_minutes + tolerance_more].

    Args:
        model: The cp_model.CpModel() instance.
        employees_target_minutes: List of employees names with their target
            target working time in minutes.
        shifts: Dictionary or map of (employee_id, day_id, shift_id) -> BoolVar.
        num_days: Number of days.
        num_shifts: Number of shifts per day.
        shift_durations: Dictionary mapping shift_id -> duration_in_minutes.
        tolerance_minutes: Allowed deviation (+/-) from target_minutes.
    """

    employees_target_minutes = target_min_data["employees"]
    shift_durations = target_min_data["shift_durations"]
    tolerance_less = target_min_data["tolerance_less"]
    tolerance_more = target_min_data["tolerance_more"]

    employee_names_to_target = {
        employees_target_minutes[i]["name"]: employees_target_minutes[i]["target"]
        for i in range(len(employees_target_minutes))
    }

    shift_index_to_name = ["F", "S", "N"]

    employees_without_information = []  # no target minutes provided
    for n_idx, employee in enumerate(employees):  # all employees
        if (
            employee["name"] not in employee_names_to_target.keys()
        ):  # check if target provided
            employees_without_information.append(employee["name"])
            continue  # skip if no target time provided
        else:
            target_minutes = employee_names_to_target[employee["name"]]
            work_time_terms = []
            for d_idx in range(num_days):
                for s_idx in range(num_shifts):
                    var = shifts[(n_idx, d_idx, s_idx)]  # this is a BoolVar (0 or 1)
                    duration = shift_durations[
                        shift_index_to_name[s_idx]
                    ]  # duration in minutes for shift s
                    work_time_terms.append(var * duration)

            total_work_time = model.NewIntVar(
                0,
                int(max(shift_durations.values()) * num_days),
                f"total_work_time_nurse_{n_idx}",
            )
            model.Add(total_work_time == sum(work_time_terms))

            model.Add(total_work_time <= target_minutes + tolerance_more)
            model.Add(total_work_time >= target_minutes - tolerance_less)

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)

    if len(employees_without_information) > 0:
        print(
            "Warning: "
            "For the following employees no target working time was provided: "
            f"'{', '.join(employees_without_information)}'."
        )
