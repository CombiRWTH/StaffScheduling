from . import Variable, EmployeeDayShiftVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar


class EmployeeDayVariable(Variable):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the EmployeeDayVariable with the given employees, days, and shifts.
        This variable represents whether an employee is assigned to work on a specific day,
        considering all shifts they might work on that day.
        """
        super().__init__()
        self._employees = employees
        self._days = days
        self._shifts = shifts

    def create(self, model: CpModel, variables: dict[str, IntVar]) -> list[IntVar]:
        vars = []
        for employee in self._employees:
            for day in self._days:
                var = model.new_bool_var(EmployeeDayVariable.get_key(employee, day))
                model.add_max_equality(
                    var,
                    [
                        variables[
                            EmployeeDayShiftVariable.get_key(employee, day, shift)
                        ]
                        for shift in self._shifts
                    ],
                )
                vars.append(var)

        return vars

    def get_key(employee: Employee, day: Day) -> str:
        return f"e:{employee.get_id()}_d:{day}"
