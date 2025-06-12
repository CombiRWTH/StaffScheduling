from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel
from datetime import timedelta


class TargetWorkingTimeConstraint(Constraint):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__("minimum-rest-time", employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            for day in self._days[:-1]:
                late_today = variables[
                    EmployeeDayShiftVariable.get_key(employee, day, self._shifts[1])
                ]
                not_early_tomorrow = variables[
                    EmployeeDayShiftVariable.get_key(
                        employee, day + timedelta(1), self._shifts[0]
                    )
                ].Not()
                model.add_implication(late_today, not_early_tomorrow)
