from datetime import timedelta

from ortools.sat.python.cp_model import CpModel, IntVar, BoolVarT

from typing import cast

from day import Day
from employee import Employee
from shift import Shift

from ..variables import EmployeeDayShiftVariable, EmployeeDayVariable, Variable
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

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            if employee.hidden:
                continue

            for day in self._days[:-1]:
                night_shift_today_variable = cast(
                    BoolVarT, variables[EmployeeDayShiftVariable.get_key(employee, day, self._shifts[Shift.NIGHT])]
                )
                night_shift_tomorrow_variable = cast(
                    BoolVarT,
                    variables[
                        EmployeeDayShiftVariable.get_key(employee, day + timedelta(1), self._shifts[Shift.NIGHT])
                    ],
                )
                day_tomorrow_variable = cast(
                    IntVar, variables[EmployeeDayVariable.get_key(employee, day + timedelta(1))]
                )

                model.add(day_tomorrow_variable == 0).only_enforce_if(
                    night_shift_today_variable, night_shift_tomorrow_variable.Not()
                )
