from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import RoundsInEarlyShiftConstraint
from src.cp.model import Model
from src.employee import Employee
from src.shift import Shift


def find_rounds_in_early_shifts_violations(solver: CpSolver, model: Model) -> list[dict[str, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

    violations: list[dict[str, int]] = []

    qualified_employees: list[Employee] = [employee for employee in employees if employee.qualified("rounds")]
    for day in [day for day in days if day.weekday() not in [5, 6]]:
        var_keys = [shift_assignment_variables[employee][day][shifts[Shift.EARLY]] for employee in qualified_employees]
        if sum([solver.value(var) for var in var_keys]) == 0:
            violations.append({cast(IntVar, var).name: solver.value(var) for var in var_keys})
    return violations


def test_rounds_in_early_shifts_1(setup: Model):
    model = setup

    constrain = RoundsInEarlyShiftConstraint(model.employees, model.days, model.shifts)
    model.add_constraint(constrain)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    violations = find_rounds_in_early_shifts_violations(solver, model)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
