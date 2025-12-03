from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import VacationDaysAndShiftsConstraint
from src.cp.variables import EmployeeDayShiftVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift


def find_vaction_days_and_shifts_violations(
    solver: CpSolver, variables_dict: dict[str, IntVar], employees: list[Employee], days: list[Day], shifts: list[Shift]
) -> list[dict[str, int]]:
    var_solution_dict: dict[str, int] = {variable.name: solver.value(variable) for variable in variables_dict.values()}
    violations: list[dict[str, int]] = []

    for employee in employees:
        for day in employee.vacation_days:
            d: dict[str, int] = {}

            var_keys = [
                EmployeeDayShiftVariable.get_key(employee, days[0] + timedelta(day - 1), shift) for shift in shifts
            ]
            if 1 in [var_solution_dict[key] for key in var_keys]:
                if day != 1:
                    k = EmployeeDayShiftVariable.get_key(employee, days[0] + timedelta(day - 2), shifts[Shift.NIGHT])
                    d = d | {k: var_solution_dict[k]}
                d = d | {key: var_solution_dict[key] for key in var_keys}
                violations.append(d)
                continue

            if day != 1:
                k = EmployeeDayShiftVariable.get_key(employee, days[0] + timedelta(day - 2), shifts[Shift.NIGHT])
                if var_solution_dict[k] == 1:
                    d = d | {k: var_solution_dict[k]} | {key: var_solution_dict[key] for key in var_keys}
                    violations.append(d)
                    continue

    for employee in employees:
        for day, shift in employee.vacation_shifts:
            key = EmployeeDayShiftVariable.get_key(
                employee, days[0] + timedelta(day - 1), shifts[Shift.SHIFT_MAPPING[shift]]
            )
            if var_solution_dict[key] == 1:
                violations.append({key: var_solution_dict[key]})

    return violations


def test_vaction_days_and_shifts_1(
    setup: tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts = setup

    constrain = VacationDaysAndShiftsConstraint(employees, days, shifts)
    constrain.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_vaction_days_and_shifts_violations(solver, variables_dict, employees, days, shifts)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
