from . import Objective
from ..variables import EmployeeDayVariable
from employee import Employee
from day import Day
from ortools.sat.python.cp_model import CpModel, IntVar
from datetime import timedelta


class NotTooManyConsecutiveDaysObjective(Objective):
    def __init__(
        self,
        max_consecutive_shifts: int,
        weight: float,
        employees: list[Employee],
        days: list[Day],
    ):
        super().__init__("not-too-many-consecutive-shifts", weight, employees, days, [])

        self.max_consecutive_shifts = max_consecutive_shifts

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        for employee in self._employees:
            for day in self._days[: -self.max_consecutive_shifts + 1]:
                variable = model.new_bool_var(f"overwork_e:{employee.get_id()}_d:{day}")
                window = [
                    variables[EmployeeDayVariable.get_key(employee, day + timedelta(i))]
                    for i in range(self.max_consecutive_shifts)
                ]
                model.add(sum(window) == self.max_consecutive_shifts).only_enforce_if(
                    variable
                )
                model.add(sum(window) != self.max_consecutive_shifts).only_enforce_if(
                    variable.Not()
                )
