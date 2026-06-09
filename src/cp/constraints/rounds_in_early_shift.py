import logging

from ortools.sat.python.cp_model import CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift
from src.station import Station

from ..constants import WEEKDAYS
from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .constraint import Constraint


class RoundsInEarlyShiftConstraint(Constraint):
    @property
    def KEY(self) -> str:
        return "rounds-in-early-shift"

    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift], stations: list[Station]):
        super().__init__(employees, days, shifts, stations)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ):
        qualified_employees = [employee for employee in self._employees if employee.qualified("rounds")]

        if not qualified_employees:
            logging.warning("No employees qualified for rounds")
            return

        for station in self._stations:
            for day in self._days:
                if day.isoweekday() in WEEKDAYS:
                    early_shift_variables = [
                        shift_assignment_variables[employee][day][self._shifts[Shift.EARLY]][station]
                        for employee in qualified_employees
                    ]

                    model.add_at_least_one(early_shift_variables)
