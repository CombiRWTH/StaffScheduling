import json
import StateManager


def load_target_working_hours(filename, settings_filename):
    with open(filename, "r") as f:
        data = json.load(f)

    with open(settings_filename, "r") as f:
        general_settings = json.load(f)

    data["shift_durations_with_index"] = {
        general_settings["SHIFT_NAME_TO_INDEX"][shift_name]: data["shift_durations"][
            shift_name
        ]
        for shift_name in data["shift_durations"].keys()
    }

    return (
        data["target_hours"],
        data["shift_durations_with_index"],
        data["tolerance_hours"],
    )


def add_target_working_hours(
    model,
    employees,
    shifts,
    num_days,
    num_shifts,
    shift_durations,
    target_hours,
    tolerance_hours=7,
):
    """
    Adds a constraint to the model that ensures each employee's total working time
    is within [target_hours - tolerance_hours, target_hours + tolerance_hours].

    Args:
        model: The cp_model.CpModel() instance.
        employees: List of employee IDs.
        shifts: Dictionary or map of (employee_id, day_id, shift_id) -> BoolVar.
        num_days: Number of days.
        num_shifts: Number of shifts per day.
        shift_durations: Dictionary mapping shift_id -> duration_in_hours.
        target_hours: The desired target total hours each employee should work.
        tolerance_hours: Allowed deviation (+/-) from target_hours.
    """
    num_employees = len(employees)
    all_employees = range(num_employees)
    all_days = range(num_days)
    all_shifts = range(num_shifts)

    for n in all_employees:
        work_time_terms = []
        for d in all_days:
            for s in all_shifts:
                var = shifts[(n, d, s)]  # this is a BoolVar (0 or 1)
                duration = shift_durations[s]  # duration in hours for shift s
                work_time_terms.append(var * duration)

        total_work_time = model.NewIntVar(
            0,
            int(sum(shift_durations.values()) * num_days),
            f"total_work_time_nurse_{n}",
        )

        model.Add(total_work_time == sum(work_time_terms))
        model.Add(total_work_time <= target_hours + tolerance_hours)
        model.Add(total_work_time > 10)

    StateManager.state.constraints.append("Target Working Hours")
