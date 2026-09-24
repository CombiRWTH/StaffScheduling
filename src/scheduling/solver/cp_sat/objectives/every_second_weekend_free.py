from collections import defaultdict
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class EverySecondWeekendFree:
    """
    Penalize consecutive weekends with the same status.

    A weekend is considered free only when the employee is not assigned on
    either Saturday or Sunday. Alternating worked and free weekends is therefore
    preferred.
    """

    id: ClassVar[str] = "every_second_weekend_free"

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        weekends = self._complete_weekends(ctx)
        if len(weekends) < 2:
            return ()

        assignment_variables_by_employee_and_date: defaultdict[
            tuple[int, date],
            list[cp_model.IntVar],
        ] = defaultdict(list)

        for (
            employee_id,
            _planning_unit_id,
            assignment_date,
            _shift_id,
            _qualification_level,
        ), variable in ctx.assignment_variables.items():
            assignment_variables_by_employee_and_date[(employee_id, assignment_date)].append(variable)

        employee_ids = sorted(
            {employee_id for employee_id, _planning_unit_id, _date, _shift_id, _level in ctx.assignment_variables}
        )

        same_status_variables: list[cp_model.IntVar] = []

        for employee_id in employee_ids:
            weekend_free_variables: list[cp_model.IntVar] = []

            for weekend_index, (saturday, sunday) in enumerate(weekends):
                weekend_assignment_variables = (
                    assignment_variables_by_employee_and_date[(employee_id, saturday)]
                    + assignment_variables_by_employee_and_date[(employee_id, sunday)]
                )

                weekend_worked = ctx.model.new_bool_var(f"esw_worked_e{employee_id}_w{weekend_index}")

                if weekend_assignment_variables:
                    ctx.model.add_max_equality(
                        weekend_worked,
                        weekend_assignment_variables,
                    )
                else:
                    ctx.model.add(weekend_worked == 0)

                weekend_free = ctx.model.new_bool_var(f"esw_free_e{employee_id}_w{weekend_index}")
                ctx.model.add(weekend_free + weekend_worked == 1)

                weekend_free_variables.append(weekend_free)

            for weekend_index in range(len(weekend_free_variables) - 1):
                current_weekend_free = weekend_free_variables[weekend_index]
                next_weekend_free = weekend_free_variables[weekend_index + 1]

                different_status = ctx.model.new_bool_var(f"esw_different_e{employee_id}_w{weekend_index}")
                ctx.model.add_abs_equality(
                    different_status,
                    current_weekend_free - next_weekend_free,
                )

                same_status = ctx.model.new_bool_var(f"esw_same_e{employee_id}_w{weekend_index}")
                ctx.model.add(same_status + different_status == 1)

                same_status_variables.append(same_status)

        if not same_status_variables:
            return ()

        total = ctx.model.new_int_var(
            0,
            len(same_status_variables),
            "esw_total",
        )
        ctx.model.add(total == sum(same_status_variables))

        return (
            Penalty(
                objective_id=self.id,
                name="total",
                expression=total,
            ),
        )

    @staticmethod
    def _complete_weekends(ctx: SolverContext) -> tuple[tuple[date, date], ...]:
        weekends: list[tuple[date, date]] = []

        current_date = ctx.dataset.planning_month.start
        end_date = ctx.dataset.planning_month.end

        while current_date <= end_date:
            if current_date.isoweekday() == 6:
                sunday = current_date + timedelta(days=1)

                if sunday <= end_date:
                    weekends.append((current_date, sunday))

            current_date += timedelta(days=1)

        return tuple(weekends)

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()
