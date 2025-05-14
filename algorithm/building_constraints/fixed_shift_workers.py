from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "Fixed Shift Workers"

# THIS IS A WORK IN PROGRESS AND NOT READY


def add_fixed_shift_workers(
    model: cp_model.CpModel,
    shifts: dict[tuple, cp_model.IntVar],
    num_shifts,
    fixed_shift_workers: dict,
    num_days,
) -> None:
    for n, fixed_shift in fixed_shift_workers.items():
        for d in range(num_days):
            # if the worker works that day
            is_working = model.NewBoolVar(f"is_working_n{n}_d{d}")
            model.Add(is_working == shifts[(n, d, fixed_shift)])

            # All non-fixed shifts are set to 0
            for s in range(num_shifts):
                if s != fixed_shift:
                    model.Add(shifts[(n, d, s)] == 0)

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
