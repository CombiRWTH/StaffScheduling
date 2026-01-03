from datetime import timedelta
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class NotTooManyConsecutiveDaysObjective(Objective):
    @property
    def KEY(self) -> str:
        return "not-too-many-consecutive-days"

    def __init__(
        self,
        max_consecutive_shifts: int,
        weight: float,
        employees: list[Employee],
        days: list[Day],
    ):
        """
        Initializes the objective that minimizes the number of consecutive shifts for employees.
        """
        super().__init__(weight, employees, days, [])

        self.max_consecutive_shifts = max_consecutive_shifts

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        possible_overwork_variables: list[IntVar] = []
        for employee in self._employees:
            for day in self._days[: -self.max_consecutive_shifts]:
                day_phase_variable = model.new_bool_var(f"day_phase_e:{employee.get_key()}_d:{day}")
                window = [
                    employee_works_on_day_variables[employee][day + timedelta(i)]
                    for i in range(self.max_consecutive_shifts + 1)
                ]
                model.add(sum(window) == self.max_consecutive_shifts + 1).only_enforce_if(day_phase_variable)
                model.add(sum(window) != self.max_consecutive_shifts + 1).only_enforce_if(day_phase_variable.Not())

                possible_overwork_variables.append(day_phase_variable)

        return cast(LinearExpr, sum(possible_overwork_variables)) * self._weight
