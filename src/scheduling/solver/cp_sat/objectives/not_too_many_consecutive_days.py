from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date as Date
from datetime import timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class NotTooManyConsecutiveDays:
    """
    Adds a penalty to the solver for assigning more than MAX_CONSECUTIVE_DAYS
    consecutively to an employee.
    """

    id: ClassVar[str] = "not_too_many_consecutive_days"
    MAX_CONSECUTIVE_DAYS: int = 5

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        # Group decision variables by (employee, date)
        vars_by_employee_date: defaultdict[tuple[int, Date], list[cp_model.IntVar]] = defaultdict(list)
        for key, variable in ctx.assignment_variables.items():
            employee_id, _, assignment_date, _, _ = key
            vars_by_employee_date[(employee_id, assignment_date)].append(variable)

        employee_ids = sorted({emp_id for emp_id, *_ in ctx.assignment_variables})
        planning_dates = self._planning_dates(ctx)

        window_length = self.MAX_CONSECUTIVE_DAYS + 1
        if len(planning_dates) < window_length:
            return ()

        # Create boolean 'worked_day' variables for each (employee, date)
        worked_day_vars: dict[tuple[int, Date], cp_model.IntVar] = {}
        for employee_id in employee_ids:
            for current_date in planning_dates:
                day_vars = vars_by_employee_date.get((employee_id, current_date), [])
                worked_day_vars[(employee_id, current_date)] = self._get_worked_variable(
                    ctx,
                    day_vars,
                    name=f"ntmcd__worked_e{employee_id}_d{current_date}",
                )

        # Apply sliding-window penalties of length (MAX_CONSECUTIVE_DAYS + 1)
        penalties: list[cp_model.IntVar] = []
        number_of_windows = len(planning_dates) - window_length + 1

        for employee_id in employee_ids:
            for start_index in range(number_of_windows):
                window_dates = planning_dates[start_index : start_index + window_length]
                window_worked_vars = [worked_day_vars[(employee_id, w_date)] for w_date in window_dates]

                # Penalty triggers if employee works ALL days in the window
                exceeded_var = ctx.model.new_bool_var(f"ntmcd__exceeded_e{employee_id}_d{window_dates[0]}")

                ctx.model.add_bool_and(window_worked_vars).only_enforce_if(exceeded_var)  # pyright: ignore[reportUnknownMemberType]
                ctx.model.add_bool_or([v.Not() for v in window_worked_vars]).only_enforce_if(exceeded_var.Not())  # pyright: ignore[reportUnknownMemberType]

                penalties.append(exceeded_var)

        if not penalties:
            return ()

        return (
            Penalty(
                objective_id=self.id,
                name="total_too_many_consecutive_days",
                expression=cp_model.LinearExpr.sum(penalties),  # pyright: ignore[reportUnknownMemberType]
            ),
        )

    @staticmethod
    def _get_worked_variable(ctx: SolverContext, variables: Sequence[cp_model.IntVar], *, name: str) -> cp_model.IntVar:
        worked = ctx.model.new_bool_var(name)
        if variables:
            ctx.model.add_max_equality(worked, list(variables))
        else:
            ctx.model.add(worked == 0)
        return worked

    @staticmethod
    def _planning_dates(ctx: SolverContext) -> tuple[Date, ...]:
        dates: list[Date] = []
        current_date = ctx.dataset.planning_month.start
        end_date = ctx.dataset.planning_month.end

        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)

        return tuple(dates)

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        return ()
