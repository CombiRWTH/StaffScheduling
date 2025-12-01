import os
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar
from test_free_day_after_night_shift_phase import find_free_day_after_night_shift_phase_violations
from test_hierarchy_of_intermediate_shifts import find_hierarchy_of_intermediate_shifts_violations
from test_max_one_shift_per_day import find_max_one_shift_per_day_violations
from test_min_rest_time import find_min_rest_time_violations
from test_min_staffing import find_min_staffing_violations
from test_planned_shifts import find_planned_shifts_violations
from test_rounds_in_early_shifts import find_rounds_in_early_shifts_violations
from test_target_working_time import find_target_working_time_violations
from test_vaction_days_and_shifts import find_vaction_days_and_shifts_violations

from src.cp.constraints import (
    FreeDayAfterNightShiftPhaseConstraint,
    HierarchyOfIntermediateShiftsConstraint,
    MaxOneShiftPerDayConstraint,
    MinRestTimeConstraint,
    MinStaffingConstraint,
    PlannedShiftsConstraint,
    RoundsInEarlyShiftConstraint,
    TargetWorkingTimeConstraint,
    VacationDaysAndShiftsConstraint,
)
from src.cp.variables import Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift

# class SolutionPrinter(CpSolverSolutionCallback):
#     def __init__(self):
#         super().__init__()
#         self.solution_count = 0

#     def on_solution_callback(self):
#         self.solution_count += 1
#         print(f"Solution {self.solution_count} at t={self.WallTime():.3f}s \n")


def test_free_day_after_night_shift_phase_1(
    setup_case_77: tuple[
        CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift], dict[str, dict[str, dict[str, int]]]
    ],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts, min_staffing = setup_case_77

    FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts).create(
        model, cast(dict[str, Variable], variables_dict)
    )
    HierarchyOfIntermediateShiftsConstraint(employees, days, shifts).create(
        model, cast(dict[str, Variable], variables_dict)
    )
    MaxOneShiftPerDayConstraint(employees, days, shifts).create(model, cast(dict[str, Variable], variables_dict))
    MinRestTimeConstraint(employees, days, shifts).create(model, cast(dict[str, Variable], variables_dict))
    MinStaffingConstraint(min_staffing, employees, days, shifts).create(
        model, cast(dict[str, Variable], variables_dict)
    )
    PlannedShiftsConstraint(employees, days, shifts).create(model, cast(dict[str, Variable], variables_dict))
    RoundsInEarlyShiftConstraint(employees, days, shifts).create(model, cast(dict[str, Variable], variables_dict))
    TargetWorkingTimeConstraint(employees, days, shifts).create(model, cast(dict[str, Variable], variables_dict))
    VacationDaysAndShiftsConstraint(employees, days, shifts).create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 0
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.linearization_level = 0
    # cb = SolutionPrinter()
    solver.solve(model)  # ,cb)

    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")

    free_day_after_night_shift_phase_violations = find_free_day_after_night_shift_phase_violations(
        solver, variables_dict, employees, days, shifts
    )
    hierarchy_of_intermediate_shifts_violations = find_hierarchy_of_intermediate_shifts_violations(
        solver, variables_dict, employees, days, shifts
    )
    max_one_shift_per_day_violations = find_max_one_shift_per_day_violations(
        solver, variables_dict, employees, days, shifts
    )
    min_rest_time_violations = find_min_rest_time_violations(solver, variables_dict, employees, days, shifts)
    min_staffing_violations = find_min_staffing_violations(
        solver, variables_dict, employees, days, shifts, min_staffing
    )
    planned_shifts_violations = find_planned_shifts_violations(solver, variables_dict, employees, days, shifts)
    rounds_in_early_shifts_violations = find_rounds_in_early_shifts_violations(
        solver, variables_dict, employees, days, shifts
    )
    target_working_time_violations = find_target_working_time_violations(
        solver, variables_dict, employees, days, shifts
    )
    vaction_days_and_shifts_violations = find_vaction_days_and_shifts_violations(
        solver, variables_dict, employees, days, shifts
    )

    violations = {
        "free_day_after_night_shift_phase_violations": free_day_after_night_shift_phase_violations,
        "hierarchy_of_intermediate_shifts_violations": hierarchy_of_intermediate_shifts_violations,
        "max_one_shift_per_day_violations": max_one_shift_per_day_violations,
        "min_rest_time_violations": min_rest_time_violations,
        "min_staffing_violations": min_staffing_violations,
        "planned_shifts_violations": planned_shifts_violations,
        "rounds_in_early_shifts_violations": rounds_in_early_shifts_violations,
        "target_working_time_violations": target_working_time_violations,
        "vaction_days_and_shifts_violations": vaction_days_and_shifts_violations,
    }

    def detailed_error_display(violations: dict[str, list[dict[str, int]]]) -> str:
        result = "\n\n\n#######################################\n"

        for violation_name, violation in violations.items():
            result = result + "\n--------- |" + violation_name + "| = " + str(len(violation)) + " -----------\n"

            for dict in violation:
                result = result + "\n" + pformat(dict) + "\n"

            result = result + "\n----------------------------------------------------\n"

        result = result + "\n#######################################\n\n\n"

        end = ""
        for violation_name, violation in violations.items():
            end = end + "\n|" + violation_name + "| = " + str(len(violation))
        result = result + end

        # save file in the same directory
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(__location__, "output_test_all_constraints.txt"), "w") as f:
            f.write(str(result))

        return end

    assert sum(len(v) for _, v in violations.items()) == 0, detailed_error_display(violations)
