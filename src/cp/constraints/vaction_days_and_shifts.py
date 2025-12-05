from datetime import timedelta

from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint


class VacationDaysAndShiftsConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "vacation-days-and-shifts"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures employees do not have shifts on their vacation days.
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
                if employee.unavailable(day):
                    day_variable = employee_works_on_day_variables[employee][day]
                    model.add(day_variable == 0)

                    # what about holidays starting at the beginning of a month?
                    if day.day > 1:
                        night_shift_variable = shift_assignment_variables[employee][day - timedelta(1)][
                            self._shifts[Shift.NIGHT]
                        ]
                        model.add(night_shift_variable == 0)

                for shift in self._shifts:
                    if employee.unavailable(day, shift):
                        shift_variable = shift_assignment_variables[employee][day][shift]
                        model.add(shift_variable == 0)
