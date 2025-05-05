import json
import StateManager


def load_min_number_of_staff(filename):
    with open(filename, "r") as f:
        return json.load(f)["requirements"]


def add_min_number_of_staff(model, employees, shifts, requirements):
    employeeidx_by_type = {}
    for idx, employee in enumerate(employees):
        employeeidx_by_type.setdefault(employee["type"], []).append(idx)

    for req in requirements:
        day = req["day"]
        shift = req["shift"]
        for staff_type, required_count in req["required"].items():
            if staff_type not in employeeidx_by_type:
                continue
            relevant_employees = employeeidx_by_type[staff_type]
            work_vars = [shifts[(n, day, shift)] for n in relevant_employees]
            model.Add(sum(work_vars) == required_count)

    StateManager.state.constraints.append("Minimal Number of Staff")
