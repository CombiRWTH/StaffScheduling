import os
from pprint import pformat

from ortools.sat.python.cp_model import CpSolver
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
from src.cp.model import Model


def test_free_day_after_night_shift_phase_1(
    setup_case_77: tuple[Model, dict[str, dict[str, dict[str, int]]]],
):
    model, min_staffing = setup_case_77
    none_hidden_employees = [e for e in model.employees if not e.hidden]

    employees = model.employees
    days = model.days
    shifts = model.shifts

    model.add_constraint(FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts))
    model.add_constraint(HierarchyOfIntermediateShiftsConstraint(employees, days, shifts))
    model.add_constraint(MaxOneShiftPerDayConstraint(employees, days, shifts))
    model.add_constraint(MinRestTimeConstraint(employees, days, shifts))
    model.add_constraint(MinStaffingConstraint(min_staffing, employees, days, shifts))
    model.add_constraint(PlannedShiftsConstraint(employees, days, shifts))
    model.add_constraint(RoundsInEarlyShiftConstraint(employees, days, shifts))
    model.add_constraint(TargetWorkingTimeConstraint(employees, days, shifts))
    model.add_constraint(VacationDaysAndShiftsConstraint(employees, days, shifts))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 0
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")

    min_staffing_violations = find_min_staffing_violations(solver, model, min_staffing)

    # Override the employees list in the model to only check violations for non-hidden employees
    model.employees = none_hidden_employees
    free_day_after_night_shift_phase_violations = find_free_day_after_night_shift_phase_violations(solver, model)
    hierarchy_of_intermediate_shifts_violations = find_hierarchy_of_intermediate_shifts_violations(solver, model)
    max_one_shift_per_day_violations = find_max_one_shift_per_day_violations(solver, model)
    min_rest_time_violations = find_min_rest_time_violations(solver, model)
    planned_shifts_violations = find_planned_shifts_violations(solver, model)
    rounds_in_early_shifts_violations = find_rounds_in_early_shifts_violations(solver, model)
    target_working_time_violations = find_target_working_time_violations(solver, model)
    vaction_days_and_shifts_violations = find_vaction_days_and_shifts_violations(solver, model)

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

    def detailed_error_display(
        violations: dict[str, list[dict[str, int]] | list[tuple[dict[str, int], int, int]]],
    ) -> str:
        result = "\n\n\n#######################################\n"

        for violation_name, violation in violations.items():
            result = result + "\n--------- |" + violation_name + "| = " + str(len(violation)) + " -----------\n"

            for dict in violation:
                result = result + "\n" + pformat(dict) + "\n"
                if violation_name == "target_working_time_violations" and isinstance(dict, tuple):
                    result += "Total Hours: " + str(dict[1])
                    result += "\nTarget Hours: " + str(dict[2])
                    result += "\nTarget Hours - Total Hours = " + str(dict[2] - dict[1])
                    result += "\nThis should be at most 7.67 hours = 460 min\n\n"

            result = result + "\n----------------------------------------------------\n"

        result = result + "\n#######################################\n\n\n"

        end = ""
        for violation_name, violation in violations.items():
            end = end + "\n|" + violation_name + "| = " + str(len(violation))
        result = end + result + end

        # save file in the same directory
        __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(__location__, "output_test_all_constraints.txt"), "w") as f:
            f.write(str(result))

        return end

    assert sum(len(v) for _, v in violations.items()) == 0, detailed_error_display(violations)
