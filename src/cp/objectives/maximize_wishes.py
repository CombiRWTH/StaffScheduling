from typing import cast

from ortools.sat.python.cp_model import CpModel, LinearExpr

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables, Variable
from .objective import Objective


class MaximizeEmployeeWishesObjective(Objective):
    @property
    def KEY(self) -> str:
        return "maximize-employee-wishes"

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        penalties: list[Variable] = []

        for employee in self._employees:
            # Wish to have specific days off
            for wish_day in employee.get_wish_days:
                for day in self._days:
                    if day.day == wish_day:
                        var = employee_works_on_day_variables[employee][day]
                        penalties.append(var)

            # Wish to have specific shifts off
            for _, abbr in employee.get_wish_shifts:
                for day in self._days:
                    shift = next((s for s in self._shifts if s.abbreviation == abbr), None)
                    if shift is None:
                        continue

                    var = shift_assignment_variables[employee][day][shift]
                    penalties.append(var)

        return cast(LinearExpr, sum(penalties)) * self.weight
