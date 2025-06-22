from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayVariable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel
from datetime import timedelta


class VacationDaysAndShiftsConstraint(Constraint):
    KEY = "vacation-days-and-shifts"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures employees do not have shifts on their vacation days.
        """
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            for day in self._days:
                if employee.unavailable(day.day):
                    day_variable = variables[EmployeeDayVariable.get_key(employee, day)]
                    model.add(day_variable == 0)

                    if day.day > 1:
                        night_shift_variable = variables[
                            EmployeeDayShiftVariable.get_key(
                                employee, day - timedelta(1), self._shifts[Shift.NIGHT]
                            )
                        ]
                        model.add(night_shift_variable == 0)

                for shift in self._shifts:
                    if employee.unavailable(day.day, shift.get_id()):
                        shift_variable = variables[
                            EmployeeDayShiftVariable.get_key(employee, day, shift)
                        ]
                        model.add(shift_variable == 0)
