from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeDayShiftVariable, Variable
from .constraint import Constraint


class RoundsInEarlyShiftConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "rounds-in-early-shift"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        qualified_employees = [employee for employee in self._employees if employee.qualified("rounds")]

        for day in self._days:
            if day.isoweekday() in [1, 2, 3, 4, 5]:
                early_shift_variables = [
                    cast(IntVar, variables[EmployeeDayShiftVariable.get_key(employee, day, self._shifts[Shift.EARLY])])
                    for employee in qualified_employees
                ]

                model.add_at_least_one(early_shift_variables)
