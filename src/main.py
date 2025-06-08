from cli import CLIParser
from loader import FSLoader
from cp import (
    Model,
    MinStaffingConstraint,
    OneShiftPerDayConstraint,
    TargetMinutesConstraint,
    EmployeeDayShiftVariable,
)
from datetime import timedelta
from calendar import monthrange


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

    variables = [EmployeeDayShiftVariable(employees, days, shifts)]
    constraints = [
        OneShiftPerDayConstraint(employees, days, shifts),
        MinStaffingConstraint(employees, days, shifts),
        TargetMinutesConstraint(employees, days, shifts),
    ]

    model = Model()
    for variable in variables:
        model.add_variable(variable)

    for constraint in constraints:
        model.add_constraint(constraint)

    model.solve()


if __name__ == "__main__":
    main()
