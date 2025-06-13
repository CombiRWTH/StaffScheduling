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
    NotTooManyConsecutiveDaysObjective,
)
from datetime import timedelta
from calendar import monthrange
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_CONSECUTIVE_DAYS = 5


def main():
    cli = CLIParser()
    case_id = cli.get_case_id()
    start_date = cli.get_start_date()

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
        FreeDaysNearWeekendObjective(1.0, employees, days),
        MinimizeConsecutiveNightShiftsObjective(2.0, employees, days, shifts),
        NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, 1.0, employees, days),
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
        [constraint.name for constraint in constraints],
        shifts,
        solutions,
    )


if __name__ == "__main__":
    main()
