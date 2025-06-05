from model import Model
from employee import Employee
from constraints.one_shift_per_day import OneShiftPerDay


def main():
    # cli

    employees = [Employee(i, "test", "test", "abc") for i in range(3)]

    # input = FsLoader() / DbLoader()

    model = Model()
    constraints = [OneShiftPerDay(employees)]

    model.add_constraints(constraints)


if __name__ == "__main__":
    main()
