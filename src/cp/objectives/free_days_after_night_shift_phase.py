from . import Objective
from ..variables import EmployeeDayShiftVariable, EmployeeDayVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar
from datetime import timedelta


class FreeDaysAfterNightShiftPhaseObjective(Objective):
    KEY = "free-day-after-night-shift-phase"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        super().__init__(weight, employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        penalties: list[IntVar] = []

        for employee in self._employees:
            
            for day in self._days[:-2]:
                night_var = variables[
                    EmployeeDayShiftVariable.get_key(
                        employee, day, self._shifts[Shift.NIGHT]
                    )
                ]
                next_day_var = variables[
                    EmployeeDayVariable.get_key(employee, day + timedelta(days=1))
                ]
                after_next_day_var = variables[
                    EmployeeDayVariable.get_key(employee, day + timedelta(days=2))
                ]

                penalty_var = model.NewBoolVar(
                    f"penalty_after_night_{employee.get_id()}_{day}"
                )

                model.Add(penalty_var == 1).OnlyEnforceIf(
                    [night_var, next_day_var.Not(), after_next_day_var]
                )
                model.Add(penalty_var == 0).OnlyEnforceIf(night_var.Not())

                penalties.append(penalty_var)

        return sum(penalties) * self.weight
