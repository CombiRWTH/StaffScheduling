from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import HierarchyOfIntermediateShiftsConstraint
from src.cp.variables import EmployeeDayShiftVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift


def find_hierarchy_of_intermediate_shifts_violations(
    solver: CpSolver, variables_dict: dict[str, IntVar], employees: list[Employee], days: list[Day], shifts: list[Shift]
) -> list[dict[str, int]]:
    var_solution_dict: dict[str, int] = {variable.name: solver.value(variable) for variable in variables_dict.values()}
    violations: list[dict[str, int]] = []

    # [weekdays,weekenddays]
    weeks: list[tuple[list[Day], list[Day]]] = [
        (
            [day - timedelta(i) for i in range(1, 6) if day - timedelta(i) >= days[0]],
            [day, day + timedelta(1) if day - timedelta(1) <= days[-1] else day],
        )
        for day in days
        if day.weekday() == 5
    ]

    for weekdays, weekenddays in weeks:
        for weekday in weekdays:
            sum_interm_on_weekday: int = sum(
                [
                    var_solution_dict[EmployeeDayShiftVariable.get_key(employee, weekday, shifts[Shift.INTERMEDIATE])]
                    for employee in employees
                ]
            )
            for weekendday in weekenddays:
                sum_interm_on_weekendday: int = sum(
                    [
                        var_solution_dict[
                            EmployeeDayShiftVariable.get_key(employee, weekendday, shifts[Shift.INTERMEDIATE])
                        ]
                        for employee in employees
                    ]
                )

                if (
                    sum_interm_on_weekday - sum_interm_on_weekendday < 0
                    or 1 < sum_interm_on_weekday - sum_interm_on_weekendday
                ):
                    d: dict[str, int] = {}
                    for employee in employees:
                        key_weekday = EmployeeDayShiftVariable.get_key(employee, weekday, shifts[Shift.INTERMEDIATE])
                        d[key_weekday] = var_solution_dict[key_weekday]
                    for employee in employees:
                        key_weekendday = EmployeeDayShiftVariable.get_key(
                            employee, weekendday, shifts[Shift.INTERMEDIATE]
                        )
                        d[key_weekendday] = var_solution_dict[key_weekendday]
                    violations.append(d)

    return violations


def test_hierarchy_of_intermediate_shifts_1(
    setup: tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts = setup

    constrain: HierarchyOfIntermediateShiftsConstraint = HierarchyOfIntermediateShiftsConstraint(
        employees, days, shifts
    )
    constrain.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_hierarchy_of_intermediate_shifts_violations(solver, variables_dict, employees, days, shifts)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
