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

    # detect how many shifts the current model contains
    num_shifts = max(s for (_, _, s) in shifts.keys()) + 1

    # classic “not-forward” rotations
    bad_rotations = [(0, 2), (1, 0), (2, 1)]

    # extend with Z-related pairs if Z is present (index 3)
    if num_shifts >= 4:
        pass
        # I am not sure if there are like any bad rotation with Zwischendienst?
        # bad_rotations.extend(
        #     [
        #         (0, 3),  # E → Z
        #         (2, 3),  # N → Z
        #         (3, 0),  # Z → E
        #         (3, 1),  # Z → L
        #         (3, 2),  # Z → N
        #     ]
        # )

    for n in range(num_employees):
        for d in range(num_days - 1):
            for prev_s, next_s in bad_rotations:
                b = model.NewBoolVar(f"bad_rot_n{n}_d{d}_{prev_s}_to_{next_s}")
                model.AddBoolAnd(
                    [shifts[(n, d, prev_s)], shifts[(n, d + 1, next_s)]]
                ).OnlyEnforceIf(b)
                model.AddBoolOr(
                    [shifts[(n, d, prev_s)].Not(), shifts[(n, d + 1, next_s)].Not()]
                ).OnlyEnforceIf(b.Not())
                penalties.append(b)

    StateManager.state.objectives.append((sum(penalties), NAME_OF_CONSTRAINT))
    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
