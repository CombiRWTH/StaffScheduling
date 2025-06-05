from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from variables.variable import Variable
from variables.employee_day_shift import EmployeeDayShift
from ortools.sat.python.cp_model import CpModel


class MinStaffing(Constraint):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__("one-shift-per-day")

        self._employees = employees
        self._days = days
        self._shifts = shifts

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for day in self._days:
            for shift in self._shifts:
                model.add_at_least_one(
                    variables[EmployeeDayShift.get_key(employee, day, shift)]
                    for employee in self._employees
                )
