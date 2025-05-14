from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "Not to long shifts"


def add_not_too_long_shifts(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    work_on_day: dict[tuple, cp_model.IntVar],
    num_shifts,
    num_days,
) -> None:
    MAX_CONSECUTIVE_WORK_DAYS = 5
    num_employees = len(employees)

    objective_terms = []
    for n in range(num_employees):
        for d in range(num_days - MAX_CONSECUTIVE_WORK_DAYS):
            # Creation of penalty variables: continuous overwork
            overwork = model.NewBoolVar(f"overwork_n{n}_start{d}")

            # select MAX+1 days window
            window = [
                work_on_day[(n, d + i)] for i in range(MAX_CONSECUTIVE_WORK_DAYS + 1)
            ]
            model.Add(sum(window) == MAX_CONSECUTIVE_WORK_DAYS + 1).OnlyEnforceIf(
                overwork
            )
            model.Add(sum(window) != MAX_CONSECUTIVE_WORK_DAYS + 1).OnlyEnforceIf(
                overwork.Not()
            )

            # Addition of targeted penalties
            # The less punishment the better
            objective_terms.append(overwork.Not())

    StateManager.state.objectives.append((sum(objective_terms)), NAME_OF_CONSTRAINT)
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
