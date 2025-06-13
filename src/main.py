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
    NotTooManyConsecutiveDaysObjective,
    RotateShiftsForwardObjective,
)
from datetime import timedelta
from calendar import monthrange
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_CONSECUTIVE_DAYS = 5


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
    days = [
        start_date + timedelta(days=i)
        for i in range(monthrange(start_date.year, start_date.month)[1])
    ]
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
        FreeDaysNearWeekendObjective(5.0, employees, days),
        MinimizeConsecutiveNightShiftsObjective(2.0, employees, days, shifts),
        # MinimizeOvertimeObjective(1.0, employees, days, shifts),
        NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, 1.0, employees, days),
        RotateShiftsForwardObjective(1.0, employees, days, shifts),
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

    solutions = model.solve()

    loader.write_solutions(
        case_id,
        employees,
        [constraint.name for constraint in constraints + objectives],
        shifts,
        solutions,
    )


if __name__ == "__main__":
    main()
