from cli import CLIParser
from loader import FSLoader
from cp import (
    Model,
    FreeDayAfterNightShiftPhaseConstraint,
    MinRestTimeConstraint,
    MinStaffingConstraint,
    MaxOneShiftPerDayConstraint,
    TargetWorkingTimeConstraint,
    VacationDaysAndShiftsConstraint,
    EmployeeDayShiftVariable,
    EmployeeDayVariable,
    FreeDaysNearWeekendObjective,
    MinimizeConsecutiveNightShiftsObjective,
    MinimizeOvertimeObjective,
    MinimizeHiddenEmployeesObjective,
    NotTooManyConsecutiveDaysObjective,
    RotateShiftsForwardObjective,
    FreeDaysAfterNightShiftPhaseObjective,
)
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_CONSECUTIVE_DAYS = 5
TIMEOUT = 5 * 60
SOLUTIONS_LIMIT = 10


def main():
    cli = CLIParser(
        [
            FreeDayAfterNightShiftPhaseConstraint,
            MinRestTimeConstraint,
            MinStaffingConstraint,
            MaxOneShiftPerDayConstraint,
            TargetWorkingTimeConstraint,
            VacationDaysAndShiftsConstraint,
            FreeDaysNearWeekendObjective,
            MinimizeConsecutiveNightShiftsObjective,
            MinimizeHiddenEmployeesObjective,
            MinimizeOvertimeObjective,
            NotTooManyConsecutiveDaysObjective,
            RotateShiftsForwardObjective,
        ]
    )
    case_id = cli.get_case_id()
    start_date = cli.get_start_date()
    selected_constraints = cli.get_constraints()

    loader = FSLoader(case_id)

    employees = loader.get_employees()
    days = loader.get_days(start_date)
    shifts = loader.get_shifts()

    min_staffing = loader.get_min_staffing()

    variables = [
        EmployeeDayShiftVariable(employees, days, shifts),
        EmployeeDayVariable(
            employees, days, shifts
        ),  # Based on EmployeeDayShiftVariable
    ]
    constraints = [
        FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts),
        MinRestTimeConstraint(employees, days, shifts),
        MinStaffingConstraint(min_staffing, employees, days, shifts),
        MaxOneShiftPerDayConstraint(employees, days, shifts),
        TargetWorkingTimeConstraint(employees, days, shifts),
        VacationDaysAndShiftsConstraint(employees, days, shifts),
    ]
    objectives = [
        FreeDaysNearWeekendObjective(10.0, employees, days),
        MinimizeConsecutiveNightShiftsObjective(2.0, employees, days, shifts),
        MinimizeHiddenEmployeesObjective(100.0, employees, days, shifts),
        MinimizeOvertimeObjective(4.0, employees, days, shifts),
        NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, 1.0, employees, days),
        RotateShiftsForwardObjective(1.0, employees, days, shifts),
        FreeDaysAfterNightShiftPhaseObjective(3.0, employees, days, shifts),
    ]

    if selected_constraints is not None:
        constraints = [
            constraint
            for constraint in constraints
            if constraint.KEY in selected_constraints
        ]
        objectives = [
            objective
            for objective in objectives
            if objective.KEY in selected_constraints
        ]

    model = Model()
    for variable in variables:
        model.add_variable(variable)

    for objective in objectives:
        model.add_objective(objective)

    for constraint in constraints:
        model.add_constraint(constraint)

    solution = model.solve(TIMEOUT)

    loader.write_solution(
        solution,
    )


if __name__ == "__main__":
    main()
