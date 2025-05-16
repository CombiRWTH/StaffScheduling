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
    shift_names_to_index = {"F": 0, "S": 1, "N": 2}

    if "employees" in constraints:
        for employee in constraints["employees"]:
            employee_idx = name_to_index[employee["name"]]
            if "free_days" in employee:
                for day_int in employee[
                    "free_days"
                ]:  # day_int corresponds to real date, starts at 1
                    for s in range(num_shifts):
                        model.Add(
                            shifts[(employee_idx, day_int - 1, s)] == 0
                        )  # day_int to day_idx
                    model.Add(
                        shifts[(employee_idx, day_int - 2, 2)] == 0
                    )  # no night shift before vacation
            if "free_shifts" in employee:
                for day_int, shift_name in employee["free_shifts"]:
                    shift_idx = shift_names_to_index[shift_name]
                    model.Add(shifts[(employee_idx, day_int - 1, shift_idx)] == 0)
    else:
        raise ValueError(
            "Dataformat `free shifts` does not fit. Key `employees` is missing."
        )

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
