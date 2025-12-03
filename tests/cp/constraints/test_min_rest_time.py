from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import MinRestTimeConstraint
from src.cp.variables import EmployeeDayShiftVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift


def find_min_rest_time_violations(
    solver: CpSolver, variables_dict: dict[str, IntVar], employees: list[Employee], days: list[Day], shifts: list[Shift]
) -> list[dict[str, int]]:
    var_solution_dict: dict[str, int] = {variable.name: solver.value(variable) for variable in variables_dict.values()}
    violations: list[dict[str, int]] = []

    first_day_shifts: list[tuple[int, Shift]] = [
        (1, Shift(shift.id, shift.name, shift.start_time, shift.end_time))
        if shift.start_time < shift.end_time
        else (1, Shift(shift.id, shift.name, shift.start_time, shift.end_time + 1440))
        for shift in shifts
    ]
    second_day_shifts: list[tuple[int, Shift]] = [
        (2, Shift(shift.id, shift.name, shift.start_time + 1440, shift.end_time + 1440))
        for (_, shift) in first_day_shifts
    ]
    total_shifts = first_day_shifts + second_day_shifts

    for employee in employees:
        for day in days[:-1]:
            for i1, first_shift in total_shifts:
                for i2, second_shift in total_shifts:
                    if first_shift.start_time > second_shift.start_time:
                        continue
                    if second_shift.start_time - first_shift.end_time >= 9 * 60:
                        continue
                    if first_shift == second_shift:
                        continue
                    key_first_shift_var = EmployeeDayShiftVariable.get_key(
                        employee, day + timedelta(i1 - 1), shifts[first_shift.id]
                    )
                    key_second_shift_var = EmployeeDayShiftVariable.get_key(
                        employee, day + timedelta(i2 - 1), shifts[second_shift.id]
                    )
                    if var_solution_dict[key_first_shift_var] and var_solution_dict[key_second_shift_var]:
                        d: dict[str, int] = {}
                        d[key_first_shift_var] = var_solution_dict[key_first_shift_var]
                        d[key_second_shift_var] = var_solution_dict[key_second_shift_var]
                        violations.append(d)
    return violations


def test_min_rest_time_1(
    setup: tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts = setup

    constrain = MinRestTimeConstraint(employees, days, shifts)
    constrain.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_min_rest_time_violations(solver, variables_dict, employees, days, shifts)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
