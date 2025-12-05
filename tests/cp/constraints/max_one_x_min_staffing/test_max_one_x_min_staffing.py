from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import (
    MaxOneShiftPerDayConstraint,
    MinStaffingConstraint,
)
from src.cp.variables import Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift
from tests.cp.constraints import test_max_one_shift_per_day, test_min_staffing


def test_max_one_x_min_staffing_1(
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

    constrain1 = MaxOneShiftPerDayConstraint(employees, days, shifts)
    constrain1.create(model, cast(dict[str, Variable], variables_dict))
    constrain2 = MinStaffingConstraint(min_staffing, employees, days, shifts)
    constrain2.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations1 = test_max_one_shift_per_day.find_max_one_shift_per_day_violations(
        solver, variables_dict, employees, days, shifts
    )
    violations2 = test_min_staffing.find_min_staffing_violations(
        solver, variables_dict, employees, days, shifts, min_staffing
    )

    violations = violations1 + violations2
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
