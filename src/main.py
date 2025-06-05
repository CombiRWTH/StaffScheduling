from cli import CLIParser
from loader import FSLoader
from cp import (
    Model,
    MinStaffingConstraint,
    OneShiftPerDayConstraint,
    EmployeeDayShiftVariable,
)
from shift import Shift
from datetime import date, timedelta


def main():
    cli = CLIParser()
    case_id = cli.get_case_id()
    loader = FSLoader(case_id)

    employees = loader.get_employees()

    # input = FsLoader() / DbLoader()
    days = [
        date.today(),
        date.today() + timedelta(days=1),
        date.today() + timedelta(days=2),
    ]
    shifts = [Shift("Früh", 1), Shift("Spät", 2), Shift("Nacht", 3)]

    variables = [EmployeeDayShiftVariable(employees, days, shifts)]
    constraints = [
        OneShiftPerDayConstraint(employees, days, shifts),
        MinStaffingConstraint(employees, days, shifts),
    ]

    model = Model()
    for variable in variables:
        model.add_variable(variable)

    for constraint in constraints:
        model.add_constraint(constraint)

    model.solve()


if __name__ == "__main__":
    main()
