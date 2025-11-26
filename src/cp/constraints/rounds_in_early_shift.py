from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint


class RoundsInEarlyShiftConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "rounds-in-early-shift"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__(employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ):
        qualified_employees = [employee for employee in self._employees if employee.qualified("rounds")]

        for day in self._days:
            if day.isoweekday() in [1, 2, 3, 4, 5]:
                early_shift_variables = [
                    shift_assignment_variables[employee][day][self._shifts[Shift.EARLY]]
                    for employee in qualified_employees
                ]

                model.add_at_least_one(early_shift_variables)
