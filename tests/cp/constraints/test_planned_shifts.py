from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import PlannedShiftsConstraint
from src.cp.model import Model
from src.shift import Shift


def find_planned_shifts_violations(solver: CpSolver, model: Model) -> list[dict[str, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

    violations: list[dict[str, int]] = []

    for employee in employees:
        for day_index, shift_str in employee.get_planned_shifts:
            day = days[0] + timedelta(day_index - 1)
            if shift_str not in Shift.SHIFT_MAPPING:
                continue
            shift = shifts[Shift.SHIFT_MAPPING[shift_str]]
            var = shift_assignment_variables[employee][day][shift]
            if solver.value(var) != 1:
                violations.append({cast(IntVar, var).name: solver.value(var)})
    return violations


def test_planned_shifts_1(setup: Model):
    model = setup

    constrain = PlannedShiftsConstraint(model.employees, model.days, model.shifts)
    model.add_constraint(constrain)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    violations = find_planned_shifts_violations(solver, model)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
