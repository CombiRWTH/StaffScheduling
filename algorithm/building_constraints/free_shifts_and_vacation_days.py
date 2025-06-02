import StateManager
from ortools.sat.python import cp_model

NAME_OF_CONSTRAINT = "free shifts and vacation days"


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
            if "vacation_days" in employee:
                for day_int in employee[
                    "vacation_days"
                ]:  # day_int corresponds to real date, starts at 1
                    for s in range(num_shifts):
                        model.Add(
                            shifts[(employee_idx, day_int - 1, s)] == 0
                        )  # day_int to day_idx
                    if day_int >= 2:  # prevent index of -1
                        model.Add(
                            shifts[(employee_idx, day_int - 2, 2)] == 0
                        )  # no night shift before vacation

            # forbidden = not vacation, but regular days which the person does not work
            if "forbidden_days" in employee:
                for day_int in employee["forbidden_days"]:
                    for s in range(num_shifts):
                        model.Add(
                            shifts[(employee_idx, day_int - 1, s)] == 0
                        )  # day_int to day_idx

            if (
                "vacation_shifts" in employee
                and len(employee["vacation_shifts"][0]) > 0
            ):
                for day_int, shift_name in employee["vacation_shifts"]:
                    shift_idx = shift_names_to_index[shift_name]
                    model.Add(shifts[(employee_idx, day_int - 1, shift_idx)] == 0)

            # currently handled the same as vacation shifts
            if (
                "forbidden_shifts" in employee
                and len(employee["forbidden_shifts"][0]) > 0
            ):
                for day_int, shift_name in employee["forbidden_shifts"]:
                    shift_idx = shift_names_to_index[shift_name]
                    model.Add(shifts[(employee_idx, day_int - 1, shift_idx)] == 0)

            # whishes
            if "wish_days" in employee:
                for day_int in employee[
                    "wish_days"
                ]:  # day_int corresponds to real date, starts at 1
                    for s in range(num_shifts):
                        model.Add(
                            shifts[(employee_idx, day_int - 1, s)] == 0
                        )  # day_int to day_idx
                    if day_int >= 2:  # prevent index of -1
                        model.Add(
                            shifts[(employee_idx, day_int - 2, 2)] == 0
                        )  # no night shift before vacation
            if "wish_shifts" in employee and len(employee["wish_shifts"][0]) > 0:
                for day_int, shift_name in employee["wish_shifts"]:
                    shift_idx = shift_names_to_index[shift_name]
                    model.Add(shifts[(employee_idx, day_int - 1, shift_idx)] == 0)

    else:
        raise ValueError(
            "Dataformat `free shifts` does not fit. Key `employees` is missing."
        )

    StateManager.state.constraints.append(NAME_OF_CONSTRAINT)
