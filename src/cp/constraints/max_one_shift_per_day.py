from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar

from day import Day
from employee import Employee
from shift import Shift

from ..variables import EmployeeDayShiftVariable, Variable
from .constraint import Constraint


class MaxOneShiftPerDayConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "one-shift-per-day"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures an employee has at most one shift per day.
        """
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            if employee.hidden:
                continue

            for day in self._days:
                model.add_at_most_one(
                    cast(IntVar, variables[EmployeeDayShiftVariable.get_key(employee, day, shift)])
                    for shift in self._shifts
                )
