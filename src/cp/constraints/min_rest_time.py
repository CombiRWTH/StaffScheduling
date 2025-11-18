from datetime import timedelta
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeDayShiftVariable, Variable
from .constraint import Constraint


class MinRestTimeConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "minimum-rest-time"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures an employee has a minimum rest time between shifts.
        """
        super().__init__(employees, days, shifts)

    # what about early and night shift on the same day, does that fulfill the reqiurement?
    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            if employee.hidden:
                continue

            for day in self._days[:-1]:
                late_today = cast(
                    IntVar, variables[EmployeeDayShiftVariable.get_key(employee, day, self._shifts[Shift.LATE])]
                )
                early_tomorrow_key = EmployeeDayShiftVariable.get_key(
                    employee, day + timedelta(1), self._shifts[Shift.EARLY]
                )
                not_early_tomorrow = cast(IntVar, variables[early_tomorrow_key]).Not()
                model.add_implication(late_today, not_early_tomorrow)
