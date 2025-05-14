import json
import StateManager
from ortools.sat.python import cp_model

NAME_OF_CONSTRAINT = "free shifts and vacation days"


def load_free_shifts_and_vacation_days(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data


def add_free_shifts_and_vacation_days(
    model: cp_model.CpModel,
    employees: list[dict],
    shifts: dict[tuple, cp_model.IntVar],
    constraints: dict,
    num_shifts: int,
) -> None:
    """
    Adds constraints for requested days off and shift exclusions.
    """
    name_to_index = {employee["name"]: idx for idx, employee in enumerate(employees)}

    if "time_off" in constraints:
        for request in constraints["time_off"]:
            employee_idx = name_to_index[request["name"]]
            if "days_off" in request:
                for day_int in request[
                    "days_off"
                ]:  # day_int is real day, starts at 1 not zero
                    for s in range(num_shifts):
                        model.Add(
                            shifts[(employee_idx, day_int - 1, s)] == 0
                        )  # day_int needs to be changed to day_idx
                    model.Add(
                        shifts[(employee_idx, day_int - 1, 2)] == 0
                    )  # no night shift before vacation

            if "shifts_off" in request:
                for day_int, shift in request["shifts_off"]:
                    model.Add(shifts[(employee_idx, day_int - 1, shift)] == 0)

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
