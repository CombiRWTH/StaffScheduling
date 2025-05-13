from ortools.sat.python import cp_model
import StateManager


def add_not_too_long_shifts(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_shifts,
    num_days,
) -> None:
    MAX_CONSECUTIVE_WORK_DAYS = 5
    num_employees = len(employees)
    work = {}
    for n in range(num_employees):
        for d in range(num_days):
            work[(n, d)] = model.NewBoolVar(f"work_n{n}_d{d}")
            model.AddMaxEquality(
                work[(n, d)], [shifts[(n, d, s)] for s in range(num_shifts)]
            )
    objective_terms = []
    for n in range(num_employees):
        for d in range(num_days - MAX_CONSECUTIVE_WORK_DAYS):
            # Creation of penalty variables: continuous overwork
            overwork = model.NewBoolVar(f"overwork_n{n}_start{d}")

            # select MAX+1 days window
            window = [work[(n, d + i)] for i in range(MAX_CONSECUTIVE_WORK_DAYS + 1)]
            model.Add(sum(window) == MAX_CONSECUTIVE_WORK_DAYS + 1).OnlyEnforceIf(
                overwork
            )
            model.Add(sum(window) != MAX_CONSECUTIVE_WORK_DAYS + 1).OnlyEnforceIf(
                overwork.Not()
            )

            # Addition of targeted penalties
            # The less punishment the better
            objective_terms.append(overwork.Not())
    model.Minimize(sum(objective_terms))
    StateManager.state.constraints.append("not too long shifts")
