from . import Objective
from ..variables import EmployeeDayShiftVariable, EmployeeDayVariable
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, IntVar


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
        penalties = []

        night_shifts = [
            shift for shift in self._shifts if shift.get_id() == Shift.NIGHT
        ]

        for employee in self._employees:
            for i in range(len(self._days) - 1):
                current_day = self._days[i]
                next_day = self._days[i + 1]

                for night_shift in night_shifts:
                    night_key = EmployeeDayShiftVariable.get_key(
                        employee, current_day, night_shift
                    )

                    is_night = variables[night_key]
                    next_day_key = EmployeeDayVariable.get_key(employee, next_day)

                    is_penalty = model.NewBoolVar(
                        f"penalty_day_after_night_{employee.get_id()}_{current_day}"
                    )

                    model.Add(variables[next_day_key] == 1).OnlyEnforceIf(is_penalty)
                    model.Add(variables[next_day_key] != 1).OnlyEnforceIf(
                        is_penalty.Not()
                    )

                    model.AddHint(is_penalty, 0)
                    model.AddHint(is_night, 0)

                    penalties.append(is_penalty)

        return sum(penalties) * self.weight
