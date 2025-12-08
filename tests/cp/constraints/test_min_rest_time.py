from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import MinRestTimeConstraint
from src.cp.model import Model
from src.cp.variables import Variable
from src.shift import Shift


def find_min_rest_time_violations(assignment: dict[Variable, int], model: Model) -> list[dict[str, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

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
                    var_first_shift = shift_assignment_variables[employee][day + timedelta(i1 - 1)][
                        shifts[first_shift.id]
                    ]
                    var_second_shift = shift_assignment_variables[employee][day + timedelta(i2 - 1)][
                        shifts[second_shift.id]
                    ]
                    if assignment[var_first_shift] and assignment[var_second_shift]:
                        d: dict[str, int] = {}
                        d[cast(IntVar, var_first_shift).name] = assignment[var_first_shift]
                        d[cast(IntVar, var_second_shift).name] = assignment[var_second_shift]
                        violations.append(d)
    return violations


def test_min_rest_time_1(setup: Model):
    model = setup

    constrain = MinRestTimeConstraint(model.employees, model.days, model.shifts)
    model.add_constraint(constrain)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    assignment = {var: solver.Value(var) for var in model.variables}

    violations = find_min_rest_time_violations(assignment, model)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
