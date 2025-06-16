from . import Constraint
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable, EmployeeDayVariable, EmployeeDayShiftVariable
from ortools.sat.python.cp_model import CpModel
from datetime import timedelta


class FreeDayAfterNightShiftPhaseConstraint(Constraint):
    KEY = "free-day-after-night-shift-phase"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint that ensures an employee has a free day after a night shift phase.
        """
        super().__init__(employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, Variable]):
        for employee in self._employees:
            for day in self._days[:-1]:
                night_shift_today_variable = variables[
                    EmployeeDayShiftVariable.get_key(
                        employee, day, self._shifts[Shift.NIGHT]
                    )
                ]
                night_shift_tomorrow_variable = variables[
                    EmployeeDayShiftVariable.get_key(
                        employee, day + timedelta(1), self._shifts[Shift.NIGHT]
                    )
                ]
                day_tomorrow_variable = variables[
                    EmployeeDayVariable.get_key(employee, day + timedelta(1))
                ]

                model.add(day_tomorrow_variable == 0).only_enforce_if(
                    [night_shift_today_variable, night_shift_tomorrow_variable.Not()]
                )
