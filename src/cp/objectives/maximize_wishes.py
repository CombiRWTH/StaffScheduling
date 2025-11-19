from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from ..variables import EmployeeDayShiftVariable, EmployeeDayVariable, Variable
from .objective import Objective


class MaximizeEmployeeWishesObjective(Objective):
    @property
    def KEY(self) -> str:
        return "maximize-employee-wishes"

    def create(self, model: CpModel, variables: dict[str, Variable]) -> LinearExpr:
        penalties: list[IntVar] = []

        for employee in self._employees:
            # Wish to have specific days off
            for wish_day in employee.get_wish_days:
                for day in self._days:
                    if day.day == wish_day:
                        var = cast(IntVar, variables[EmployeeDayVariable.get_key(employee, day)])
                        penalty = model.NewBoolVar(f"penalty_on_assigned_wish_day_off_{employee.get_key()}_{day}")
                        model.Add(penalty == 1).OnlyEnforceIf(var)
                        model.Add(penalty == 0).OnlyEnforceIf(var.Not())
                        penalties.append(penalty)

            # Wish to have specific shifts off
            for _, abbr in employee.get_wish_shifts:
                for day in self._days:
                    shift = next((s for s in self._shifts if s.abbreviation == abbr), None)
                    if shift is None:
                        continue
                    key = EmployeeDayShiftVariable.get_key(employee, day, shift)
                    var = cast(IntVar, variables[key])
                    penalty = model.NewBoolVar(f"penalty_on_assigned_wish_shift_off_{employee.get_key()}_{day}_{abbr}")
                    model.Add(penalty == 1).OnlyEnforceIf(var)
                    model.Add(penalty == 0).OnlyEnforceIf(var.Not())
                    penalties.append(penalty)

        return cast(LinearExpr, sum(penalties)) * self.weight
