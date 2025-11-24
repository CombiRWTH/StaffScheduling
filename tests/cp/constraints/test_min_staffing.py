from pprint import pprint
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import MinStaffingConstraint
from src.cp.variables import EmployeeDayShiftVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift


def find_min_staffing_violations(
    solver: CpSolver,
    variables_dict: dict[str, IntVar],
    employees: list[Employee],
    days: list[Day],
    shifts: list[Shift],
    min_staffing: dict[str, dict[str, dict[str, int]]],
) -> list[dict[str, int]]:
    var_solution_dict: dict[str, int] = {variable.name: solver.value(variable) for variable in variables_dict.values()}
    violations: list[dict[str, int]] = []

    weekday_map: dict[str, int] = {"Mo": 0, "Di": 1, "Mi": 2, "Do": 3, "Fr": 4, "Sa": 5, "So": 6}
    # since I do not want to look up the encoding of all viable shift abbreviations, I will
    # stick with the basic ones
    shift_map: dict[str, int] = {"F": Shift.EARLY, "N": Shift.NIGHT, "S": Shift.LATE}

    for employee_level in min_staffing.keys():
        for weekday_str in min_staffing[employee_level].keys():
            for shift_str in min_staffing[employee_level][weekday_str]:
                required: int = min_staffing[employee_level][weekday_str][shift_str]
                # for every matching day inside our period
                for day in [day for day in days if day.weekday() == weekday_map[weekday_str]]:
                    relevant_var_keys = [
                        EmployeeDayShiftVariable.get_key(employee, day, shifts[shift_map[shift_str]])
                        for employee in employees
                        if employee.level == employee_level
                    ]
                    total_shifts_worked = sum([var_solution_dict[var] for var in relevant_var_keys])
                    if required > total_shifts_worked:
                        d: dict[str, int] = {}
                        for var in relevant_var_keys:
                            d[var] = var_solution_dict[var]
                        violations.append(d)
    return violations


def test_min_staffing_1(
    setup_with_minstaffing: tuple[
        CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift], dict[str, dict[str, dict[str, int]]]
    ],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts, min_staffing = setup_with_minstaffing

    constrain = MinStaffingConstraint(min_staffing, employees, days, shifts)
    constrain.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_min_staffing_violations(solver, variables_dict, employees, days, shifts, min_staffing)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, pprint(violations, width=1)
