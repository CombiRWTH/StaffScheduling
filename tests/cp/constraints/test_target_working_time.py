from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import TargetWorkingTimeConstraint
from src.cp.variables import EmployeeDayShiftVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift


def find_target_working_time_violations(
    solver: CpSolver, variables_dict: dict[str, IntVar], employees: list[Employee], days: list[Day], shifts: list[Shift]
) -> list[dict[str, int]]:
    var_solution_dict: dict[str, int] = {variable.name: solver.value(variable) for variable in variables_dict.values()}
    violations: list[dict[str, int]] = []

    for employee in employees:
        var_keys: list[str] = []
        total_hours: int = 0
        for day in days:
            for shift in shifts:
                var_keys.append(EmployeeDayShiftVariable.get_key(employee, day, shift))
                total_hours = total_hours + var_solution_dict[var_keys[-1]] * shift.duration
        if abs(total_hours - employee.target_working_time) > 460:
            violations.append({key: var_solution_dict[key] for key in var_keys})
    return violations


def test_target_working_time_1(
    setup: tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts = setup

    constrain = TargetWorkingTimeConstraint(employees, days, shifts)
    constrain.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_target_working_time_violations(solver, variables_dict, employees, days, shifts)
    assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
