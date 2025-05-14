from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "Not too many Consecutive Shifts"


def add_not_too_many_consecutive_shifts(
    model: cp_model.CpModel,
    employees: list[dict],
    work_on_day: dict[tuple, cp_model.IntVar],
    num_days,
    max_consecutive_work_days: int,
) -> None:
    num_employees = len(employees)

    objective_terms = []
    for n in range(num_employees):
        for d_idx in range(num_days - max_consecutive_work_days):
            # Creation of penalty variables: continuous overwork
            overwork = model.NewBoolVar(f"overwork_n{n}_start{d_idx}")

            # select MAX+1 days window
            window = [
                work_on_day[(n, d_idx + i)]
                for i in range(max_consecutive_work_days + 1)
            ]
            model.Add(sum(window) == max_consecutive_work_days + 1).OnlyEnforceIf(
                overwork
            )
            model.Add(sum(window) != max_consecutive_work_days + 1).OnlyEnforceIf(
                overwork.Not()
            )

            # Addition of targeted penalties
            # The less punishment the better
            objective_terms.append(overwork.Not())

    StateManager.state.objectives.append((sum(objective_terms), NAME_OF_CONSTRAINT))
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
