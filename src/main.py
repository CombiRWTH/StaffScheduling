from model import Model
from employee import Employee
from shift import Shift
from variables.employee_day_shift import EmployeeDayShift
from constraints import MinStaffing, OneShiftPerDay
from datetime import date, timedelta


def main():
    # cli
    # input = FsLoader() / DbLoader()

    employees = [Employee(i, "test_{i}", "test", "abc") for i in range(3)]
    days = [
        date.today(),
        date.today() + timedelta(days=1),
        date.today() + timedelta(days=2),
    ]
    shifts = [Shift("Früh", 1), Shift("Spät", 2), Shift("Nacht", 3)]

    variables = [EmployeeDayShift(employees, days, shifts)]
    constraints = [
        OneShiftPerDay(employees, days, shifts),
        MinStaffing(employees, days, shifts),
    ]

    model = Model()
    for variable in variables:
        model.add_variable(variable)

    for constraint in constraints:
        model.add_constraint(constraint)

    model.solve()


if __name__ == "__main__":
    main()
