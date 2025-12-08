from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import MinStaffingConstraint
from src.cp.model import Model
from src.cp.variables import Variable
from src.shift import Shift


def find_min_staffing_violations(
    assignment: dict[Variable, int], model: Model, min_staffing: dict[str, dict[str, dict[str, int]]]
) -> list[dict[str, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

    violations: list[dict[str, int]] = []

    weekday_map: dict[str, int] = {"Mo": 0, "Di": 1, "Mi": 2, "Do": 3, "Fr": 4, "Sa": 5, "So": 6}

    for employee_level in min_staffing.keys():
        for weekday_str in min_staffing[employee_level].keys():
            for shift_str in min_staffing[employee_level][weekday_str]:
                required: int = min_staffing[employee_level][weekday_str][shift_str]
                # for every matching day inside our period
                for day in [day for day in days if day.weekday() == weekday_map[weekday_str]]:
                    relevant_var = [
                        shift_assignment_variables[employee][day][shifts[Shift.SHIFT_MAPPING[shift_str]]]
                        for employee in employees
                        if employee.level == employee_level
                    ]
                    total_shifts_worked = sum([assignment[var] for var in relevant_var])
                    if required > total_shifts_worked:
                        d: dict[str, int] = {}
                        for var in relevant_var:
                            d[cast(IntVar, var).name] = assignment[var]
                        violations.append(d)
    return violations


def test_min_staffing_1(setup_with_minstaffing: tuple[Model, dict[str, dict[str, dict[str, int]]]]):
    model, min_staffing = setup_with_minstaffing

    constrain = MinStaffingConstraint(min_staffing, model.employees, model.days, model.shifts)
    model.add_constraint(constrain)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    assignment = {var: solver.Value(var) for var in model.variables}

    violations = find_min_staffing_violations(assignment, model, min_staffing)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
