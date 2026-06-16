from datetime import timedelta
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift
from src.station import Station

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class FreeDaysAfterNightShiftPhaseObjective(Objective):
    @property
    def KEY(self) -> str:
        return "free-day-after-night-shift-phase"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
        stations: list[Station],
    ):
        super().__init__(weight, employees, days, shifts, stations)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        penalties: list[IntVar] = []

        for employee in self._employees:
            for day in self._days[:-2]:
                station_vars = [
                    shift_assignment_variables[employee][day][self._shifts[Shift.NIGHT]][station]
                    for station in self._stations
                ]

                night_var = model.new_bool_var(f"night_shift_{employee.get_key()}_{day}")

                model.add_max_equality(night_var, station_vars)

                next_day_var = employee_works_on_day_variables[employee][day + timedelta(days=1)]
                after_next_day_var = employee_works_on_day_variables[employee][day + timedelta(days=2)]
                penalty_var = model.new_bool_var(f"free_days_after_night_{employee.get_key()}_{day}")

                model.add(penalty_var == 1).only_enforce_if([night_var, next_day_var.Not(), after_next_day_var])
                model.add(penalty_var == 0).only_enforce_if(night_var.Not())

                penalties.append(penalty_var)

        return cast(LinearExpr, sum(penalties) * self.weight)
