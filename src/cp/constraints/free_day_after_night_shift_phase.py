from datetime import timedelta

from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..constants import SPECIAL_NIGHT_SHIFT_INDEX
from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint


class FreeDayAfterNightShiftPhaseConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "free-day-after-night-shift-phase"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        super().__init__(employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> None:
        regular_night_shift = self._find_shift_by_id(Shift.NIGHT)
        special_night_shift = self._find_shift_by_id(SPECIAL_NIGHT_SHIFT_INDEX)

        night_shifts = [shift for shift in (regular_night_shift, special_night_shift) if shift is not None]

        if not night_shifts:
            return

        for employee in self._employees:
            for day in self._days[:-1]:
                tomorrow = day + timedelta(days=1)
                day_tomorrow_variable = employee_works_on_day_variables[employee][tomorrow]

                night_shift_today_variables = [
                    shift_assignment_variables[employee][day][shift] for shift in night_shifts
                ]
                night_shift_tomorrow_variables = [
                    shift_assignment_variables[employee][tomorrow][shift] for shift in night_shifts
                ]

                for night_shift_today_variable in night_shift_today_variables:
                    model.add(day_tomorrow_variable == 0).only_enforce_if(
                        [
                            night_shift_today_variable,
                            *[
                                night_shift_tomorrow_variable.Not()
                                for night_shift_tomorrow_variable in night_shift_tomorrow_variables
                            ],
                        ]
                    )

    def _find_shift_by_id(self, shift_id: int) -> Shift | None:
        return next((shift for shift in self._shifts if shift.get_id() == shift_id), None)
