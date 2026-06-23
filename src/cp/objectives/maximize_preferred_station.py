from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift
from src.station import Station

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class MaximizePreferredStationObjective(Objective):
    @property
    def KEY(self) -> str:
        return "maximize_preferred_station"

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
        not_preferred_station_vars: list[IntVar] = []

        for employee in self._employees:
            preferred_station = employee.get_preferred_station
            if preferred_station == 408 or preferred_station is None or employee.hidden:  # 408 is the springerpool
                continue

            for day in self._days:
                for shift in self._shifts:
                    for station in self._stations:
                        if station == preferred_station:
                            variable = shift_assignment_variables[employee][day][shift][station]
                            if station != preferred_station:
                                not_preferred_station_vars.append(variable)

        return cast(LinearExpr, sum(not_preferred_station_vars)) * self._weight
