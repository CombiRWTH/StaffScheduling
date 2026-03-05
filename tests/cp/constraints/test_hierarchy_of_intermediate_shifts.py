from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import HierarchyOfIntermediateShiftsConstraint
from src.cp.model import Model
from src.cp.variables import Variable
from src.day import Day
from src.shift import Shift


def find_hierarchy_of_intermediate_shifts_violations(
    assignment: dict[Variable, int], model: Model
) -> list[dict[str, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

    violations: list[dict[str, int]] = []

    # [weekdays,weekenddays]
    weeks: list[tuple[list[Day], list[Day]]] = [
        (
            [day - timedelta(i) for i in range(1, 6) if day - timedelta(i) >= days[0]],
            [day, day + timedelta(1) if day + timedelta(1) <= days[-1] else day],
        )
        for day in days
        if day.weekday() == 5
    ]

    for weekdays, weekenddays in weeks:
        for weekday in weekdays:
            sum_interm_on_weekday: int = sum(
                [
                    assignment[shift_assignment_variables[employee][weekday][shifts[Shift.INTERMEDIATE]]]
                    for employee in employees
                ]
            )
            for weekendday in weekenddays:
                sum_interm_on_weekendday: int = sum(
                    [
                        assignment[shift_assignment_variables[employee][weekendday][shifts[Shift.INTERMEDIATE]]]
                        for employee in employees
                    ]
                )

                if (
                    sum_interm_on_weekday - sum_interm_on_weekendday < 0
                    or 1 < sum_interm_on_weekday - sum_interm_on_weekendday
                ):
                    d: dict[str, int] = {}
                    for employee in employees:
                        var_weekday = shift_assignment_variables[employee][weekday][shifts[Shift.INTERMEDIATE]]
                        d[cast(IntVar, var_weekday).name] = assignment[var_weekday]
                    for employee in employees:
                        var_weekendday = shift_assignment_variables[employee][weekendday][shifts[Shift.INTERMEDIATE]]
                        d[cast(IntVar, var_weekendday).name] = assignment[var_weekendday]
                    violations.append(d)

    return violations


def test_hierarchy_of_intermediate_shifts_1(setup: Model):
    model = setup

    constrain: HierarchyOfIntermediateShiftsConstraint = HierarchyOfIntermediateShiftsConstraint(
        model.employees, model.days, model.shifts
    )
    model.add_constraint(constrain)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    assignment = {var: solver.Value(var) for var in model.variables}

    violations = find_hierarchy_of_intermediate_shifts_violations(assignment, model)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
