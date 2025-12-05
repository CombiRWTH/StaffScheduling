from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import VacationDaysAndShiftsConstraint
from src.cp.model import Model
from src.shift import Shift


def find_vaction_days_and_shifts_violations(solver: CpSolver, model: Model) -> list[dict[str, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

    violations: list[dict[str, int]] = []

    for employee in employees:
        for day in employee.vacation_days:
            d: dict[str, int] = {}

            var_keys = [shift_assignment_variables[employee][days[0] + timedelta(day - 1)][shift] for shift in shifts]
            if 1 in [solver.value(var) for var in var_keys]:
                if day != 1:
                    k = shift_assignment_variables[employee][days[0] + timedelta(day - 2)][shifts[Shift.NIGHT]]
                    d = d | {cast(IntVar, k).name: solver.value(k)}
                d = d | {cast(IntVar, var).name: solver.value(var) for var in var_keys}
                violations.append(d)
                continue

            if day != 1:
                k = shift_assignment_variables[employee][days[0] + timedelta(day - 2)][shifts[Shift.NIGHT]]
                if solver.value(k) == 1:
                    d = (
                        d
                        | {cast(IntVar, k).name: solver.value(k)}
                        | {cast(IntVar, var).name: solver.value(var) for var in var_keys}
                    )
                    violations.append(d)
                    continue

    for employee in employees:
        for day, shift in employee.vacation_shifts:
            var = shift_assignment_variables[employee][days[0] + timedelta(day - 1)][shifts[Shift.SHIFT_MAPPING[shift]]]
            if solver.value(var) == 1:
                violations.append({cast(IntVar, var).name: solver.value(var)})

    return violations


def test_vaction_days_and_shifts_1(
    setup: Model,
):
    model = setup
    constraint = VacationDaysAndShiftsConstraint(model.employees, model.days, model.shifts)
    model.add_constraint(constraint)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    violations = find_vaction_days_and_shifts_violations(solver, model)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
