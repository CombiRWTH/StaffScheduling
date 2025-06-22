from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel


class MaxOneShiftPerDayConstraint(Constraint):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__("one-shift-per-day", employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            for day in self._days:
                model.add_at_most_one(
                    variables[EmployeeDayShiftVariable.get_key(employee, day, shift)]
                    for shift in self._shifts
                )
