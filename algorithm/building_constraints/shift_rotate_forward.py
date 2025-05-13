import json
from ortools.sat.python import cp_model
import algorithm.StateManager as StateManager


def load_shift_rotate_forward(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def add_shift_rotate_forward(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_shifts,
    fixed_shift_workers: dict,
    num_days
) -> None:
    num_employees = len(employees)
    for n, fixed_shift in fixed_shift_workers.items():
        for d in range(num_days):
            # if the worker works that day
            is_working = model.NewBoolVar(f'is_working_n{n}_d{d}')
            model.Add(is_working == shifts[(n, d, fixed_shift)])

            # All non-fixed shifts are set to 0
            for s in range(num_shifts):
                if s != fixed_shift:
                    model.Add(shifts[(n, d, s)] == 0)

    penalties = []

    bad_rotations = [(0, 2), (1, 0), (2, 1)]  # non-forward rotate

    for n in range(num_employees):
        if n in fixed_shift_workers:
            continue  # ignore fixed shifts worker

        for d in range(num_days - 1):
            for (prev_s, next_s) in bad_rotations:
                b = model.NewBoolVar(f'bad_rot_n{n}_d{d}_from{prev_s}to{next_s}')
                model.AddBoolAnd([shifts[(n, d, prev_s)], shifts[(n, d + 1, next_s)]]).OnlyEnforceIf(b)
                model.AddBoolOr([shifts[(n, d, prev_s)].Not(), shifts[(n, d + 1, next_s)].Not()]).OnlyEnforceIf(b.Not())
                penalties.append(b)
    model.Minimize(sum(penalties))
    StateManager.state.constraints.append("Shift should rotate forward")
