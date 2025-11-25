from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import RoundsInEarlyShiftConstraint
from src.cp.variables import EmployeeDayShiftVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift


def find_rounds_in_early_shifts_violations(
    solver: CpSolver, variables_dict: dict[str, IntVar], employees: list[Employee], days: list[Day], shifts: list[Shift]
) -> list[dict[str, int]]:
    var_solution_dict: dict[str, int] = {variable.name: solver.value(variable) for variable in variables_dict.values()}
    violations: list[dict[str, int]] = []

    qualified_employees: list[Employee] = [employee for employee in employees if employee.qualified("rounds")]
    for day in [day for day in days if day.weekday() not in [5, 6]]:
        var_keys = [
            EmployeeDayShiftVariable.get_key(employee, day, shifts[Shift.EARLY]) for employee in qualified_employees
        ]
        if sum([var_solution_dict[key] for key in var_keys]) == 0:
            violations.append({key: var_solution_dict[key] for key in var_keys})
    return violations


def test_rounds_in_early_shifts_1(
    setup: tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts = setup

    constrain = RoundsInEarlyShiftConstraint(employees, days, shifts)
    constrain.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_rounds_in_early_shifts_violations(solver, variables_dict, employees, days, shifts)
    assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
