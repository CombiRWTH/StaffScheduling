from . import Objective
from ..variables import EmployeeDayVariable
from employee import Employee
from day import Day
from ortools.sat.python.cp_model import CpModel, IntVar
from datetime import timedelta


class NotTooManyConsecutiveDaysObjective(Objective):
    KEY = "not-too-many-consecutive-shifts"

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

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        possible_overwork_variables: list[IntVar] = []
        for employee in self._employees:
            for day in self._days[: -self.max_consecutive_shifts]:
                day_phase_variable = model.new_bool_var(
                    f"day_phase_e:{employee.get_id()}_d:{day}"
                )
                window = [
                    variables[EmployeeDayVariable.get_key(employee, day + timedelta(i))]
                    for i in range(self.max_consecutive_shifts + 1)
                ]
                model.add(
                    sum(window) == self.max_consecutive_shifts + 1
                ).only_enforce_if(day_phase_variable)
                model.add(
                    sum(window) != self.max_consecutive_shifts + 1
                ).only_enforce_if(day_phase_variable.Not())

                possible_overwork_variables.append(day_phase_variable)

        return sum(possible_overwork_variables) * self.weight
