from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr

from ..variables import (
    EmployeeWorksOnDayVariables,
    ShiftAssignmentVariables,
    Variable,
)
from .objective import Objective


class MinimizeWishPenaltyRangeObjective(Objective):
    @property
    def KEY(self) -> str:
        return "minimize-wish-penalty-range"

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        # Stores the total penalty score for each employee
        employee_penalties: list[IntVar] = []

        for employee in self._employees:
            # Stores all wish violations of a single employee
            penalty_vars: list[Variable] = []

            # Penalty if an employee has to work on a wished off day
            for wish_day in employee.get_wish_days:
                for day in self._days:
                    if day.day == wish_day:
                        var = employee_works_on_day_variables[employee][day]
                        penalty_vars.append(var)

            # Penalty if an employee is assigned to a wished off shift
            for _, abbr in employee.get_wish_shifts:
                for day in self._days:
                    shift = next(
                        (s for s in self._shifts if s.abbreviation == abbr),
                        None,
                    )

                    if shift is None:
                        continue

                    var = shift_assignment_variables[employee][day][shift]
                    penalty_vars.append(var)

            # Total wish penalty of this employee
            employee_penalty = model.new_int_var(
                0,
                max(1, len(penalty_vars)),
                f"wish_penalty_{employee.get_key()}",
            )

            model.add(
                employee_penalty == sum(penalty_vars)
            )

            employee_penalties.append(employee_penalty)

        # Maximum penalty among all employees
        max_penalty = model.new_int_var(
            0,
            1000,
            "max_wish_penalty",
        )

        # Minimum penalty among all employees
        min_penalty = model.new_int_var(
            0,
            1000,
            "min_wish_penalty",
        )

        model.add_max_equality(
            max_penalty,
            employee_penalties,
        )

        model.add_min_equality(
            min_penalty,
            employee_penalties,
        )

        # Fairness metric:
        # range = max penalty - min penalty
        penalty_range = model.new_int_var(
            0,
            1000,
            "wish_penalty_range",
        )

        model.add(
            penalty_range == max_penalty - min_penalty
        )

        # Minimize the range of wish penalties
        return cast(LinearExpr, penalty_range) * self.weight