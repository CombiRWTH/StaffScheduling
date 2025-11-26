from datetime import timedelta

from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint


class FreeDayAfterNightShiftPhaseConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "free-day-after-night-shift-phase"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures an employee has a free day after a night shift phase.
        """
        super().__init__(employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> None:
        # This function falsely ignores special night shifts

        for employee in self._employees:
            if employee.hidden:
                continue

            for day in self._days[:-1]:
                night_shift_today_variable = shift_assignment_variables[employee][day][self._shifts[Shift.NIGHT]]
                night_shift_tomorrow_variable = shift_assignment_variables[employee][day + timedelta(1)][
                    self._shifts[Shift.NIGHT]
                ]
                day_tomorrow_variable = employee_works_on_day_variables[employee][day + timedelta(1)]
                # where are day_tomorrow_variables enforced? this may be the cause of the bug menitioned in the docs
                model.add(day_tomorrow_variable == 0).only_enforce_if(
                    night_shift_today_variable, night_shift_tomorrow_variable.Not()
                )
