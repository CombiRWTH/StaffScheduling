from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel
from datetime import timedelta


class MinRestTimeConstraint(Constraint):
    KEY = "minimum-rest-time"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures an employee has a minimum rest time between shifts.
        """
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            for day in self._days[:-1]:
                late_today = variables[
                    EmployeeDayShiftVariable.get_key(
                        employee, day, self._shifts[Shift.LATE]
                    )
                ]
                not_early_tomorrow = variables[
                    EmployeeDayShiftVariable.get_key(
                        employee, day + timedelta(1), self._shifts[Shift.EARLY]
                    )
                ].Not()
                model.add_implication(late_today, not_early_tomorrow)
