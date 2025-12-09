from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import TargetWorkingTimeConstraint
from src.cp.model import Model
from src.cp.variables import Variable


def find_target_working_time_violations(
    assignment: dict[Variable, int], model: Model
) -> list[tuple[dict[str, int], int, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

    violations: list[tuple[dict[str, int], int, int]] = []

    for employee in employees:
        var_keys: list[Variable] = []
        total_hours: int = 0
        for day in days:
            for shift in shifts:
                var = shift_assignment_variables[employee][day][shift]
                var_keys.append(var)
                total_hours = total_hours + assignment[var] * shift.duration
        if abs(total_hours - employee.get_available_working_time()) > 460:
            violations.append(
                (
                    {cast(IntVar, var).name: assignment[var] for var in var_keys},
                    total_hours,
                    employee.get_available_working_time(),
                )
            )
    return violations


def test_target_working_time_1(setup: Model):
    model = setup

    constrain = TargetWorkingTimeConstraint(model.employees, model.days, model.shifts)
    model.add_constraint(constrain)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    assignment = {var: solver.Value(var) for var in model.variables}

    violations = find_target_working_time_violations(assignment, model)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
