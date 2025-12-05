from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import MaxOneShiftPerDayConstraint
from src.cp.model import Model
from src.cp.variables import Variable


def find_max_one_shift_per_day_violations(assignment: dict[Variable, int], model: Model) -> list[dict[str, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

    violations: list[dict[str, int]] = []

    for employee in employees:
        for day in days:
            shift_variable_values = [assignment[shift_assignment_variables[employee][day][shift]] for shift in shifts]
            if sum(shift_variable_values) > 1:
                d: dict[str, int] = {}
                for shift in shifts:
                    var = shift_assignment_variables[employee][day][shift]
                    d[cast(IntVar, var).name] = assignment[var]
                violations.append(d)
    return violations


def test_max_one_shift_per_day_1(setup: Model):
    model = setup

    constrain: MaxOneShiftPerDayConstraint = MaxOneShiftPerDayConstraint(model.employees, model.days, model.shifts)
    model.add_constraint(constrain)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    assignment = {var: solver.Value(var) for var in model.variables}

    violations = find_max_one_shift_per_day_violations(assignment, model)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
