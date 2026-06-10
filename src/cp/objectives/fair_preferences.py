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
            violation_bools = self._get_violation_bools_for_employee(
                employee, shift_assignment_variables, employee_works_on_day_variables
            )

            if not violation_bools:
                continue

            max_possible_violations = len(violation_bools)
            total_violations = sum(violation_bools)

            tier_vars = [
                model.new_bool_var(f"tier_{i}_emp_{employee.get_key()}") for i in range(max_possible_violations)
            ]

            model.add(sum(tier_vars) == total_violations)

            for i, tier_var in enumerate(tier_vars):
                tier_weight = int((5**i) * self._weight)
                # tier_var * tier_weight creates an OR-Tools LinearExpr under the hood
                penalties.append(tier_var * tier_weight)

        return cast(LinearExpr, sum(penalties)) if penalties else None

    def _get_violation_bools_for_employee(
        self,
        employee: Employee,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> list[Variable]:
        """
        Gathers all CP-SAT boolean variables representing the employee's wishes.
        Since a wish means "I don't want to work", scheduling them (Variable == 1) counts as a violation.
        """
        violation_bools: list[Variable] = []

        # 1. Wish Days: The employee does not want to work ANY shift on these days.
        for wish_day_int in employee.get_wish_days:
            day_obj = self._find_day_by_int(wish_day_int)
            if day_obj:
                works_on_day_var = employee_works_on_day_variables[employee][day_obj]
                violation_bools.append(works_on_day_var)

        # 2. Wish Shifts: The employee does not want to work a specific shift on a specific day.
        for wish_day_int, shift_abbr in employee.get_wish_shifts:
            day_obj = self._find_day_by_int(wish_day_int)
            shift_obj = self._find_shift_by_abbr(shift_abbr)

            if day_obj and shift_obj:
                shift_var = shift_assignment_variables[employee][day_obj][shift_obj]
                violation_bools.append(shift_var)

        return violation_bools

    # --- Domain Mapping Helpers ---

    def _find_day_by_int(self, day_int: int) -> Day | None:
        """Finds the Day object matching the integer from the employee's wish list."""
        for d in self._days:
            # Matches the convention used in Employee.unavailable() -> day.day
            if getattr(d, "day", None) == day_int:
                return d
        return None

    def _find_shift_by_abbr(self, shift_abbr: str) -> Shift | None:
        """Finds the Shift object matching the string abbreviation from the employee's wish list."""
        for s in self._shifts:
            # Matches the convention used in Employee.unavailable() -> shift.abbreviation
            if getattr(s, "abbreviation", None) == shift_abbr:
                return s
        return None
