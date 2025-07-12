from . import Objective
from ..variables import EmployeeDayShiftVariable, EmployeeDayVariable
from ortools.sat.python.cp_model import CpModel, IntVar


class MaximizeEmployeeWishesObjective(Objective):
    KEY = "maximize-employee-wishes"

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        rewards: list[IntVar] = []

        for employee in self._employees:
            # Wish to be OFF on specific days
            for wish_day in employee.get_wish_days:
                for day in self._days:
                    if day.day == wish_day:
                        var = variables[EmployeeDayVariable.get_key(employee, day)]
                        wish_reward = model.NewBoolVar(
                            f"wish_day_off_{employee.get_key()}_{day}"
                        )
                        model.Add(wish_reward == 0).OnlyEnforceIf(var)
                        model.Add(wish_reward == 1).OnlyEnforceIf(var.Not())
                        rewards.append(wish_reward)

            # Wish to work specific shifts
            for wish_day, abbr in employee.get_wish_shifts:
                shift = next(
                    (s for s in self._shifts if s.abbreviation == abbr), None
                )
                key = EmployeeDayShiftVariable.get_key(employee, wish_day, shift)
                var = variables[key]
                shift_reward = model.NewBoolVar(
                    f"wish_shift_{employee.get_key()}_{wish_day}_{abbr}"
                )
                model.Add(var == 1).OnlyEnforceIf(shift_reward)
                model.Add(shift_reward == 1).OnlyEnforceIf(var)
                rewards.append(shift_reward)

        return sum(rewards) * self.weight
