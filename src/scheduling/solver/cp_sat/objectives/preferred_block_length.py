from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date as Date
from datetime import timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class PreferredBlockLength:
    """
    Adds a reward for each time an employee works a block of EXACTLY three consecutive days.
    """

    id: ClassVar[str] = "preferred_block_length"
    PREFERRED_BLOCK_LENGTH: int = 3

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
        planning_date_set = set(planning_dates)

        # Build 'worked_day' variables for each (employee, date)
        worked_day_vars: dict[tuple[int, Date], cp_model.IntVar] = {}
        for employee_id in employee_ids:
            for current_date in planning_dates:
                day_vars = vars_by_employee_date.get((employee_id, current_date), [])
                worked_day_vars[(employee_id, current_date)] = self._get_worked_variable(
                    ctx,
                    day_vars,
                    name=f"pbl__worked_e{employee_id}_d{current_date}",
                )

        block_variables: list[cp_model.IntVar] = []

        # Detect exact blocks of 3 worked days flanked by days OFF (or boundary)
        for employee_id in employee_ids:
            for start_index in range(len(planning_dates) - self.PREFERRED_BLOCK_LENGTH + 1):
                block_dates = planning_dates[start_index : start_index + self.PREFERRED_BLOCK_LENGTH]

                prev_date = block_dates[0] - timedelta(days=1)
                next_date = block_dates[-1] + timedelta(days=1)

                # Conditions required for an EXACT 3-day block
                literals: list[Any] = []

                # Middle 3 days MUST be worked
                for d in block_dates:
                    literals.append(worked_day_vars[(employee_id, d)])

                # Day before MUST be FREE (if within planning month)
                if prev_date in planning_date_set:
                    literals.append(worked_day_vars[(employee_id, prev_date)].Not())

                # Day after MUST be FREE (if within planning month)
                if next_date in planning_date_set:
                    literals.append(worked_day_vars[(employee_id, next_date)].Not())

                block_var = ctx.model.new_bool_var(f"pbl__block_e{employee_id}_d{block_dates[0]}")

                # Enforce: block_var == 1 iff ALL literals are satisfied
                ctx.model.add_bool_and(literals).only_enforce_if(block_var)  # pyright: ignore[reportUnknownMemberType]
                ctx.model.add_bool_or([lit.Not() for lit in literals]).only_enforce_if(block_var.Not())  # pyright: ignore[reportUnknownMemberType]

                block_variables.append(block_var)

        if not block_variables:
            return ()

        return (
            Penalty(
                objective_id=self.id,
                name="total_preferred_blocks",
                expression=cp_model.LinearExpr.sum(block_variables),  # pyright: ignore[reportUnknownMemberType]
                multiplier=-1,  # Negative multiplier turns penalty minimization into reward maximization
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
