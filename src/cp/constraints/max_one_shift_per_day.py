from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
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

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ):
        for employee in self._employees:
            if employee.hidden:
                continue

            for day in self._days:
                model.add_at_most_one(shift_assignment_variables[employee][day][shift] for shift in self._shifts)
