from datetime import timedelta
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar

from day import Day
from employee import Employee
from shift import Shift

from ..variables import EmployeeDayShiftVariable, EmployeeDayVariable, Variable
from .constraint import Constraint


class VacationDaysAndShiftsConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "vacation-days-and-shifts"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures employees do not have shifts on their vacation days.
        """
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            if employee.hidden:
                continue

            for day in self._days:
                if employee.unavailable(day):
                    day_variable = cast(IntVar, variables[EmployeeDayVariable.get_key(employee, day)])
                    model.add(day_variable == 0)

                    if day.day > 1:
                        night_shift_key = EmployeeDayShiftVariable.get_key(
                            employee, day - timedelta(1), self._shifts[Shift.NIGHT]
                        )
                        night_shift_variable = cast(IntVar, variables[night_shift_key])
                        model.add(night_shift_variable == 0)

                for shift in self._shifts:
                    if employee.unavailable(day, shift):
                        shift_variable = cast(IntVar, variables[EmployeeDayShiftVariable.get_key(employee, day, shift)])
                        model.add(shift_variable == 0)
