from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "Equally Distributed Workload"


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


def difference_domain_monotonic(domain):
    return sorted({a - b for a in domain for b in domain if a >= b})


def add_equally_distributed_workload_constraint(
    model: cp_model.CpModel,
    employees: list[dict],
    total_work_times: dict[str, cp_model.IntVar],
    shift_durations: dict[str, int],
    num_days: int,
) -> None:
    """Adds a constraint to equally distribute the number of shifts (workload) across all employees."""
    employee_names = [emp["name"] for emp in employees]

    domain_as_list = reachable_sums(
        shift_durations.values(), max_value=max(shift_durations.values()) * num_days
    )
    all_possible_total_minutes = cp_model.Domain.FromValues(
        domain_as_list,
    )

    # Create variables for min and max number of minutes assigned
    min_work_time = model.NewIntVarFromDomain(
        all_possible_total_minutes,
        "min_work_time",
    )
    max_work_time = model.NewIntVarFromDomain(
        all_possible_total_minutes,
        "max_work_time",
    )

    # Constrain min and max
    for name in employee_names:
        model.Add(min_work_time <= total_work_times[name])
        model.Add(max_work_time >= total_work_times[name])

    # Minimize the difference between max and min to ensure fairness
    all_possible_differences = cp_model.Domain.FromValues(
        difference_domain_monotonic(domain_as_list),
    )
    diff = model.NewIntVarFromDomain(
        all_possible_differences,
        "diff",
    )

    model.Add(diff == max_work_time - min_work_time)

    # Add objective and register constraint
    StateManager.state.objectives.append((diff, NAME_OF_CONSTRAINT))
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
