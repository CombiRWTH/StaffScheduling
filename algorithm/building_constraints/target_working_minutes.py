import StateManager
from ortools.sat.python import cp_model

NAME_OF_CONSTRAINT = "Target Working minutes"


# Idee: Einbau erstmal nur von Obergrenze
# Dann wenn zu noch Stunden übrig, Zwischendienst auffüllen
# ist ein ein Problem VIELE zwischendienste aufzufüllen und dann später manuell aufzuteilen


def reachable_sums(others, max_value):
    reachable = set()

    def dfs(current_sum):
        if current_sum > max_value:
            return
        if current_sum in reachable:
            return
        reachable.add(current_sum)
        for o in others:
            dfs(current_sum + o)

    dfs(0)  # start from zero
    return sorted(reachable)


def create_total_work_time_variables(
    model, employees, shifts, num_days, num_shifts, shift_durations
):
    shift_index_to_name = ["F", "S", "N", "Z"]

    all_possible_total_minutes = cp_model.Domain.FromValues(
        reachable_sums(
            shift_durations.values(),
            max_value=max(shift_durations.values()) * num_days,
        ),
    )

    total_work_times = {}
    for n_idx, employee in enumerate(employees):  # all employees
        work_time_terms = []
        for d_idx in range(num_days):
            for s_idx in range(num_shifts):
                var = shifts[(n_idx, d_idx, s_idx)]  # this is a BoolVar (0 or 1)
                duration = shift_durations[
                    shift_index_to_name[s_idx]
                ]  # duration in minutes for shift s
                work_time_terms.append(var * duration)

        total_work_time = model.NewIntVarFromDomain(
            all_possible_total_minutes,
            f"total_work_time_nurse_{n_idx}",
        )
        total_work_times[employee["name"]] = total_work_time
        model.Add(total_work_time == sum(work_time_terms))
    return total_work_times


def add_target_working_minutes(
    model,
    employees,
    total_work_times,
    target_min_data,
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
    tolerance_less = target_min_data["tolerance_less"]
    tolerance_more = target_min_data["tolerance_more"]

    penalty_terms = []

    employee_names_to_target = {
        employees_target_minutes[i]["name"]: employees_target_minutes[i]["target"]
        - employees_target_minutes[i]["actual"]  # SOLL - IST
        for i in range(len(employees_target_minutes))
    }

    employees_without_information = []  # no target minutes provided
    for n_idx, employee in enumerate(employees):  # all employees
        if (
            employee["name"] not in employee_names_to_target.keys()
        ):  # check if target provided
            employees_without_information.append(employee["name"])
            continue  # skip if no target time provided
        else:
            target_minutes = employee_names_to_target[employee["name"]]

            total_work_time = total_work_times[employee["name"]]

            # Hard upper bound
            model.Add(total_work_time <= target_minutes + tolerance_more)
            model.Add(total_work_time >= target_minutes - tolerance_less * 10)

            # Compute expected minimum time
            soft_min = target_minutes - tolerance_less

            # Auxiliary variable: how much the employee is underworked
            underworked = model.NewIntVar(0, soft_min, f"underworked_n{n_idx}")

            # Boolean condition: is underworked?
            is_underworked = model.NewBoolVar(f"is_underworked_n{n_idx}")

            # Link underworked only if condition is true
            model.Add(total_work_time < soft_min).OnlyEnforceIf(is_underworked)
            model.Add(total_work_time >= soft_min).OnlyEnforceIf(is_underworked.Not())

            # underworked = soft_min - total_work_time (if underworked)
            temp_diff = model.NewIntVar(0, soft_min, f"underworked_amount_n{n_idx}")
            model.Add(temp_diff == soft_min - total_work_time).OnlyEnforceIf(
                is_underworked
            )
            model.Add(temp_diff == 0).OnlyEnforceIf(is_underworked.Not())

            # Finally, bind underworked to temp_diff
            model.Add(underworked == temp_diff)

            penalty_terms += [underworked]

    StateManager.state.objectives.append((sum(penalty_terms), NAME_OF_CONSTRAINT))
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)

    if len(employees_without_information) > 0:
        print(
            "Warning: "
            "For the following employees no target working time was provided: "
            f"'{', '.join(employees_without_information)}'."
        )
