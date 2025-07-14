from . import Objective
from ..variables import EmployeeDayShiftVariable, EmployeeDayVariable
from ortools.sat.python.cp_model import CpModel, IntVar


class MaximizeEmployeeWishesObjective(Objective):
    KEY = "maximize-employee-wishes"

    def create(self, model: CpModel, variables: dict[str, IntVar]):
        penalties: list[IntVar] = []

        for employee in self._employees:
            # Wish to have specific days off
            for wish_day in employee.get_wish_days:
                for day in self._days:
                    if day.day == wish_day:
                        var = variables[EmployeeDayVariable.get_key(employee, day)]
                        penalty = model.NewBoolVar(
                            f"penalty_on_assigned_wish_day_off_{employee.get_key()}_{day}"
                        )
                        model.Add(penalty == 1).OnlyEnforceIf(var)
                        model.Add(penalty == 0).OnlyEnforceIf(var.Not())
                        penalties.append(penalty)

            # Wish to have specific shifts off
            for wish_day, abbr in employee.get_wish_shifts:
                for day in self._days:
                    shift = next(
                        (s for s in self._shifts if s.abbreviation == abbr), None
                    )
                    key = EmployeeDayShiftVariable.get_key(employee, day, shift)
                    var = variables[key]
                    penalty = model.NewBoolVar(
                        f"penalty_on_assigned_wish_shift_off_{employee.get_key()}_{day}_{abbr}"
                    )
                    model.Add(penalty == 1).OnlyEnforceIf(var)
                    model.Add(penalty == 0).OnlyEnforceIf(var.Not())
                    penalties.append(penalty)

        return sum(penalties) * self.weight
