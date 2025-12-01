from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import PlannedShiftsConstraint
from src.cp.variables import EmployeeDayShiftVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift


def find_planned_shifts_violations(
    solver: CpSolver, variables_dict: dict[str, IntVar], employees: list[Employee], days: list[Day], shifts: list[Shift]
) -> list[dict[str, int]]:
    var_solution_dict: dict[str, int] = {variable.name: solver.value(variable) for variable in variables_dict.values()}
    violations: list[dict[str, int]] = []

    for employee in employees:
        for day_index, shift_str in employee.get_planned_shifts:
            day = days[0] + timedelta(day_index - 1)
            if shift_str not in Shift.SHIFT_MAPPING:
                continue
            shift = shifts[Shift.SHIFT_MAPPING[shift_str]]
            var_key = EmployeeDayShiftVariable.get_key(employee, day, shift)
            if var_solution_dict[var_key] != 1:
                violations.append({var_key: var_solution_dict[var_key]})
    return violations


def test_planned_shifts_1(
    setup: tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts = setup

    constrain = PlannedShiftsConstraint(employees, days, shifts)
    constrain.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_planned_shifts_violations(solver, variables_dict, employees, days, shifts)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
