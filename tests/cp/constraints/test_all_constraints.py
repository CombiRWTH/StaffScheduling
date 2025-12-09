import os
import shutil
from pprint import pformat

from ortools.sat.python.cp_model import CpSolver, CpSolverSolutionCallback
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
from src.cp.objectives import (
    EverySecondWeekendFreeObjective,
    FreeDaysAfterNightShiftPhaseObjective,
    FreeDaysNearWeekendObjective,
    MaximizeEmployeeWishesObjective,
    MinimizeConsecutiveNightShiftsObjective,
    MinimizeHiddenEmployeesObjective,
    MinimizeOvertimeObjective,
    NotTooManyConsecutiveDaysObjective,
    RotateShiftsForwardObjective,
)
from src.cp.variables import Variable


def detailed_error_display(
    violations: dict[str, list[dict[str, int]] | list[tuple[dict[str, int], int, int]]],
    filename: str = "output_test_all_constraints.txt",
) -> str:
    result = "\n\n\n#######################################\n"

    for violation_name, violation in violations.items():
        result = result + "\n--------- |" + violation_name + "| = " + str(len(violation)) + " -----------\n"

        for dict in violation:
            result = result + "\n" + pformat(dict) + "\n"
            if violation_name == "target_working_time_violations" and isinstance(dict, tuple):
                result += "Total Hours: " + f"{dict[1] / 60:.2f}"
                result += "\nTarget Hours: " + f"{dict[2] / 60:.2f}"
                result += "\nTarget Hours - Total Hours = " + f"{(dict[2] - dict[1]) / 60:.2f}"
                result += "\nThis should be at most  460 min = 7.67 hours\n\n"

        result = result + "\n----------------------------------------------------\n"

    result = result + "\n#######################################\n\n\n"

    end = ""
    for violation_name, violation in violations.items():
        end = end + "\n|" + violation_name + "| = " + str(len(violation))
    result = end + result + end

    # save file in the same directory
    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    with open(os.path.join(__location__, filename), "w") as f:
        f.write(str(result))

    return end


class MultiSolutionCollector(CpSolverSolutionCallback):
    def __init__(self, model: Model, max_solutions: int = 200):
        super().__init__()
        self.assignment: list[dict[Variable, int]] = []
        self.max_solutions = max_solutions
        self.count = 0
        self.model = model

    def on_solution_callback(self):
        if self.count >= self.max_solutions:
            self.StopSearch()
            return
        self.count += 1

        self.assignment.append(
            {
                var: self.Value(var)  # type: ignore[attr-defined]
                for var in self.model.variables
            }
        )
        print(f"Found solution number {self.count:03d}")


def test_all_constraints_mass_case(
    setup_case_77: tuple[Model, dict[str, dict[str, dict[str, int]]]],
):
    model, min_staffing = setup_case_77
    none_hidden_employees = [e for e in model.employees if not e.hidden]

    employees = model.employees
    days = model.days
    shifts = model.shifts

    model.add_objective(MinimizeHiddenEmployeesObjective(100.0, employees, days, shifts))
    model.add_objective(FreeDaysNearWeekendObjective(2.0, employees, days))
    model.add_objective(MinimizeConsecutiveNightShiftsObjective(2.0, employees, days, shifts))
    model.add_objective(MinimizeHiddenEmployeesObjective(100.0, employees, days, shifts))
    model.add_objective(MinimizeOvertimeObjective(4.0, employees, days, shifts))
    model.add_objective(NotTooManyConsecutiveDaysObjective(5, 1.0, employees, days))
    model.add_objective(RotateShiftsForwardObjective(1.0, employees, days, shifts))
    model.add_objective(MaximizeEmployeeWishesObjective(3.0, employees, days, shifts))
    model.add_objective(FreeDaysAfterNightShiftPhaseObjective(3.0, employees, days, shifts))
    model.add_objective(EverySecondWeekendFreeObjective(1.0, employees, days))

    model.add_constraint(FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts))
    model.add_constraint(HierarchyOfIntermediateShiftsConstraint(employees, days, shifts))
    model.add_constraint(MaxOneShiftPerDayConstraint(employees, days, shifts))
    model.add_constraint(MinRestTimeConstraint(employees, days, shifts))
    model.add_constraint(MinStaffingConstraint(min_staffing, employees, days, shifts))
    model.add_constraint(PlannedShiftsConstraint(employees, days, shifts))
    model.add_constraint(RoundsInEarlyShiftConstraint(employees, days, shifts))
    model.add_constraint(TargetWorkingTimeConstraint(employees, days, shifts))
    model.add_constraint(VacationDaysAndShiftsConstraint(employees, days, shifts))

    model.cpModel.minimize(sum(model.penalties))
    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 0
    solver.parameters.max_time_in_seconds = 15
    solver.parameters.linearization_level = 0
    cb = MultiSolutionCollector(model)
    solver.solve(model.cpModel, cb)

    # extracting all solutions
    assignments = cb.assignment

    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")

    __location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
    subfolder_name: str = "mass_test_results"
    if os.path.exists(os.path.join(__location__, subfolder_name)):
        shutil.rmtree(os.path.join(__location__, subfolder_name))
    os.makedirs(os.path.join(__location__, subfolder_name), exist_ok=True)

    violations_list: list[dict[str, list[dict[str, int]] | list[tuple[dict[str, int], int, int]]]] = []
    for i, assignment in enumerate(assignments):
        model.employees = employees
        min_staffing_violations = find_min_staffing_violations(assignment, model, min_staffing)

        # Override the employees list in the model to only check violations for non-hidden employees
        model.employees = none_hidden_employees
        free_day_after_night_shift_phase_violations = find_free_day_after_night_shift_phase_violations(
            assignment, model
        )
        hierarchy_of_intermediate_shifts_violations = find_hierarchy_of_intermediate_shifts_violations(
            assignment, model
        )
        max_one_shift_per_day_violations = find_max_one_shift_per_day_violations(assignment, model)
        min_rest_time_violations = find_min_rest_time_violations(assignment, model)
        planned_shifts_violations = find_planned_shifts_violations(assignment, model)
        rounds_in_early_shifts_violations = find_rounds_in_early_shifts_violations(assignment, model)
        target_working_time_violations = find_target_working_time_violations(assignment, model)
        vaction_days_and_shifts_violations = find_vaction_days_and_shifts_violations(assignment, model)

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
        violations_list.append(violations)

        if len(violations) != 0:
            detailed_error_display(violations, os.path.join(subfolder_name, f"{i:03d}.txt"))

    result = ""
    for i, violations in enumerate(violations_list):
        result += f"Number Violations for result {i:03d}: {sum(len(v) for _, v in violations.items())}\n"
    with open(os.path.join(__location__, subfolder_name, "_overview.txt"), "w") as f:
        f.write(str(result))
    assert sum([sum([len(v) for _, v in violations.items()]) for violations in violations_list]) == 0, result


def test_all_constraints_single_case(
    setup_case_77: tuple[Model, dict[str, dict[str, dict[str, int]]]],
):
    model, min_staffing = setup_case_77
    none_hidden_employees = [e for e in model.employees if not e.hidden]

    employees = model.employees
    days = model.days
    shifts = model.shifts

    model.add_objective(MinimizeHiddenEmployeesObjective(100.0, employees, days, shifts))

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

    assignment = {var: solver.Value(var) for var in model.variables}

    min_staffing_violations = find_min_staffing_violations(assignment, model, min_staffing)

    # Override the employees list in the model to only check violations for non-hidden employees
    model.employees = none_hidden_employees
    free_day_after_night_shift_phase_violations = find_free_day_after_night_shift_phase_violations(assignment, model)
    hierarchy_of_intermediate_shifts_violations = find_hierarchy_of_intermediate_shifts_violations(assignment, model)
    max_one_shift_per_day_violations = find_max_one_shift_per_day_violations(assignment, model)
    min_rest_time_violations = find_min_rest_time_violations(assignment, model)
    planned_shifts_violations = find_planned_shifts_violations(assignment, model)
    rounds_in_early_shifts_violations = find_rounds_in_early_shifts_violations(assignment, model)
    target_working_time_violations = find_target_working_time_violations(assignment, model)
    vaction_days_and_shifts_violations = find_vaction_days_and_shifts_violations(assignment, model)

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

    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert sum(len(v) for _, v in violations.items()) == 0, detailed_error_display(violations)
