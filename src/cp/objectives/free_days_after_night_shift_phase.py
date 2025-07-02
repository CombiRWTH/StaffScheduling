from . import Objective
from ..variables import EmployeeDayVariable
from ortools.sat.python.cp_model import CpModel, IntVar
from datetime import timedelta
from employee import Employee
from day import Day


class FreeDaysAfterNightShiftPhaseObjective(Objective):
    KEY = "free-days-after-night-shift-phase"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list,
    ):
        """
        Objective to encourage free 48h (2 days) after a night shift phase.
        A "night phase" is 2 or more consecutive night shifts.
        """
        super().__init__(weight, employees, days, shifts)

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        penalties = []

        for employee in self._employees:
            i = 0
            while i < len(self._days) - 2:
                # Check for at least 2 consecutive night shifts
                day1 = self._days[i]
                day2 = self._days[i + 1]

                key1 = EmployeeDayVariable.get_key(employee, day1)
                key2 = EmployeeDayVariable.get_key(employee, day2)

                is_night1 = model.NewBoolVar(f"is_night1_{employee.get_id()}_{day1}")
                is_night2 = model.NewBoolVar(f"is_night2_{employee.get_id()}_{day2}")

                model.Add(variables[key1] == 3).OnlyEnforceIf(is_night1)  # shift 3 = night
                model.Add(variables[key1] != 3).OnlyEnforceIf(is_night1.Not())
                model.Add(variables[key2] == 3).OnlyEnforceIf(is_night2)
                model.Add(variables[key2] != 3).OnlyEnforceIf(is_night2.Not())

                night_phase = model.NewBoolVar(f"night_phase_{employee.get_id()}_{day1}")
                model.AddBoolAnd([is_night1, is_night2]).OnlyEnforceIf(night_phase)
                model.AddBoolOr([is_night1.Not(), is_night2.Not()]).OnlyEnforceIf(night_phase.Not())

                if i + 3 < len(self._days):
                    day3 = self._days[i + 2]
                    day4 = self._days[i + 3]

                    key3 = EmployeeDayVariable.get_key(employee, day3)
                    key4 = EmployeeDayVariable.get_key(employee, day4)

                    is_free3 = model.NewBoolVar(f"is_free3_{employee.get_id()}_{day3}")
                    is_free4 = model.NewBoolVar(f"is_free4_{employee.get_id()}_{day4}")
                    is_both_free = model.NewBoolVar(f"is_both_free_{employee.get_id()}_{day3}_{day4}")

                    model.Add(variables[key3] == 0).OnlyEnforceIf(is_free3)
                    model.Add(variables[key3] != 0).OnlyEnforceIf(is_free3.Not())
                    model.Add(variables[key4] == 0).OnlyEnforceIf(is_free4)
                    model.Add(variables[key4] != 0).OnlyEnforceIf(is_free4.Not())

                    model.AddBoolAnd([is_free3, is_free4]).OnlyEnforceIf(is_both_free)
                    model.AddBoolOr([is_free3.Not(), is_free4.Not()]).OnlyEnforceIf(is_both_free.Not())

                    penalty_var = model.NewBoolVar(f"penalty_after_night_phase_{employee.get_id()}_{day1}")
                    model.AddImplication(night_phase, penalty_var)
                    model.AddImplication(is_both_free, penalty_var.Not())

                    penalties.append(penalty_var)

                i += 1

        return sum(penalties) * self.weight
