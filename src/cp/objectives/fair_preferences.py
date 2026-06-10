from typing import cast

from ortools.sat.python.cp_model import CpModel, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables, Variable
from .objective import Objective


class FairPreferencesObjective(Objective):
    @property
    def KEY(cls) -> str:
        return "fair-preferences"

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr | None:
        penalties: list[LinearExpr] = []

        for employee in self._employees:
            day_bools, shift_bools = self._get_violation_bools_for_employee(
                employee, shift_assignment_variables, employee_works_on_day_variables
            )

            if not day_bools and not shift_bools:
                continue

            # A day wish counts as 3 strikes, so we scale the max potential violations
            # to ensure we generate enough "tier buckets" to hold the penalties.
            max_possible_violations = (len(day_bools) * 3) + len(shift_bools)

            # Here is the magic: A ruined day adds 3 strikes, a ruined shift adds 1.
            total_violations = (sum(day_bools) * 3) + sum(shift_bools)

            tier_vars = [
                model.new_bool_var(f"tier_{i}_emp_{employee.get_key()}") for i in range(max_possible_violations)
            ]

            model.add(sum(tier_vars) == total_violations)

            for i, tier_var in enumerate(tier_vars):
                # Using squares creates our steep, safe quadratic penalty curve (1, 4, 9, 16...)
                tier_weight = int(((i + 1) ** 3) * self._weight)
                penalties.append(tier_var * tier_weight)

        return cast(LinearExpr, sum(penalties)) if penalties else None

    def _get_violation_bools_for_employee(
        self,
        employee: Employee,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> tuple[list[Variable], list[Variable]]:
        day_violation_bools: list[Variable] = []
        shift_violation_bools: list[Variable] = []

        # 1. Day Wishes: Evaluates to 1 if they work ANY shift on this day.
        for wish_day_int in employee.get_wish_days:
            day_obj = self._find_day_by_int(wish_day_int)
            if day_obj:
                works_on_day_var = employee_works_on_day_variables[employee][day_obj]
                day_violation_bools.append(works_on_day_var)

        # 2. Shift Wishes: Evaluates to 1 only if they work this specific shift.
        for wish_day_int, shift_abbr in employee.get_wish_shifts:
            day_obj = self._find_day_by_int(wish_day_int)
            shift_obj = self._find_shift_by_abbr(shift_abbr)

            if day_obj and shift_obj:
                shift_var = shift_assignment_variables[employee][day_obj][shift_obj]
                shift_violation_bools.append(shift_var)

        return day_violation_bools, shift_violation_bools

    def _find_day_by_int(self, day_int: int) -> Day | None:
        """Finds the Day object matching the integer from the employee's wish list."""
        for d in self._days:
            if getattr(d, "day", None) == day_int:
                return d
        return None

    def _find_shift_by_abbr(self, shift_abbr: str) -> Shift | None:
        """Finds the Shift object matching the string abbreviation from the employee's wish list."""
        for s in self._shifts:
            if getattr(s, "abbreviation", None) == shift_abbr:
                return s
        return None
