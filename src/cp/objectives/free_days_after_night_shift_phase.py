from datetime import timedelta
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

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
    ):
        super().__init__(weight, employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        penalties: list[IntVar] = []

        for employee in self._employees:
            if employee.hidden:
                continue
            for day in self._days[:-2]:
                night_var = shift_assignment_variables[employee][day][self._shifts[Shift.NIGHT]]
                next_day_var = employee_works_on_day_variables[employee][day + timedelta(days=1)]
                after_next_day_var = employee_works_on_day_variables[employee][day + timedelta(days=2)]
                penalty_var = model.new_bool_var(f"free_days_after_night_{employee.get_key()}_{day}")

                model.add(penalty_var == 1).only_enforce_if([night_var, next_day_var.Not(), after_next_day_var])
                model.add(penalty_var == 0).only_enforce_if(night_var.Not())

                penalties.append(penalty_var)

        return cast(LinearExpr, sum(penalties) * self.weight)
