import json
from ortools.sat.python import cp_model
import StateManager

NAME_OF_CONSTRAINT = "Shifts rotate fowards"


def load_shift_rotate_forward(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def add_shift_rotate_forward(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    num_days,
) -> None:
    num_employees = len(employees)
    penalties = []
    bad_rotations = [(0, 2), (1, 0), (2, 1)]  # non-forward rotate

    for n in range(num_employees):
        # This needs to be implemented to a later time
        # fixed_shift_workers is its own constraint
        # if n in fixed_shift_workers:
        #     continue  # ignore fixed shifts worker

        for d in range(num_days - 1):
            for prev_s, next_s in bad_rotations:
                b = model.NewBoolVar(f"bad_rot_n{n}_d{d}_from{prev_s}to{next_s}")
                model.AddBoolAnd(
                    [shifts[(n, d, prev_s)], shifts[(n, d + 1, next_s)]]
                ).OnlyEnforceIf(b)
                model.AddBoolOr(
                    [shifts[(n, d, prev_s)].Not(), shifts[(n, d + 1, next_s)].Not()]
                ).OnlyEnforceIf(b.Not())
                penalties.append(b)

    StateManager.state.objectives.append((sum(penalties), NAME_OF_CONSTRAINT))
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
