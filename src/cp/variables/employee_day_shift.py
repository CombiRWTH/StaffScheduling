from ortools.sat.python.cp_model import CpModel, IntVar

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from .variable import Variable


class EmployeeDayShiftVariable(Variable):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the EmployeeDayShiftVariable with the given employees, days, and shifts.
        This variable represents whether an employee is assigned to a specific shift on a specific day.
        """
        super().__init__()
        self._employees = employees
        self._days = days
        self._shifts = shifts

    def create(self, model: CpModel, variables: dict[str, IntVar]) -> list[IntVar]:
        vars: list[IntVar] = []
        for employee in self._employees:
            for day in self._days:
                for shift in self._shifts:
                    var = model.new_bool_var(self.get_key(employee, day, shift))
                    vars.append(var)

        return vars

    @staticmethod
    def get_key(employee: Employee, day: Day, shift: Shift) -> str:
        # return f"e:{employee.get_id()}_d:{day}_s:{shift.get_id()}"
        return f"({employee.get_key()}, '{day.strftime('%Y-%m-%d')}', {shift.get_id()})"
