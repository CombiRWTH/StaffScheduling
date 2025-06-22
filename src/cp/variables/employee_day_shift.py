from .variable import Variable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar


class EmployeeDayShiftVariable(Variable):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        self._employees = employees
        self._days = days
        self._shifts = shifts

    def create(self, model: CpModel, variables: dict[str, IntVar]) -> list[IntVar]:
        vars = []
        for employee in self._employees:
            for day in self._days:
                for shift in self._shifts:
                    var = model.new_bool_var(
                        EmployeeDayShiftVariable.get_key(employee, day, shift)
                    )
                    vars.append(var)

        return vars

    def get_key(employee: Employee, day: Day, shift: Shift) -> str:
        return f"e:{employee.get_id()}_d:{day}_s:{shift.get_id()}"
