from cli import CLIParser
from loader import FSLoader
from cp import (
    Model,
    MinStaffingConstraint,
    OneShiftPerDayConstraint,
    TargetWorkingTimeConstraint,
    EmployeeDayShiftVariable,
    EmployeeDayVariable,
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
    shifts = loader.get_shifts()
    days = [
        start_date + timedelta(days=i)
        for i in range(monthrange(start_date.year, start_date.month)[1])
    ]

    variables = [
        EmployeeDayShiftVariable(employees, days, shifts),
        EmployeeDayVariable(
            employees, days, shifts
        ),  # Based on EmployeeDayShiftVariable
    ]
    constraints = [
        OneShiftPerDayConstraint(employees, days, shifts),
        MinStaffingConstraint(employees, days, shifts),
        TargetWorkingTimeConstraint(employees, days, shifts),
    ]
    objectives = [
        NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, 1.0, employees, days)
    ]

    model = Model()
    for variable in variables:
        model.add_variable(variable)

    for objective in objectives:
        model.add_objective(objective)

    for constraint in constraints:
        model.add_constraint(constraint)

    model.solve()


if __name__ == "__main__":
    main()
