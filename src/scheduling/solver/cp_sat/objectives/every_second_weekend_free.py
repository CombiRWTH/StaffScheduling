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
    Adds a penalty if two consecutive weekends have the same status (both free or both worked).
    A weekend is free only if both Saturday and Sunday are free.
    """

    id: ClassVar[str] = "every_second_weekend_free"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        weekends: list[tuple[date, date]] = []
        current = ctx.dataset.planning_month.start
        while current <= ctx.dataset.planning_month.end:
            if current.isoweekday() == 6:
                sunday = current + timedelta(days=1)
                if sunday <= ctx.dataset.planning_month.end:
                    weekends.append((current, sunday))
            current += timedelta(days=1)

        if len(weekends) < 2:
            return ()

        vars_by_employee_date: defaultdict[tuple[int, date], list[cp_model.IntVar]] = defaultdict(list)
        for (employee_id, _unit, d, _shift, _level), var in ctx.assignment_variables.items():
            vars_by_employee_date[(employee_id, d)].append(var)

        employee_ids = {key[0] for key in ctx.assignment_variables}
        penalties: list[cp_model.IntVar] = []

        for employee_id in employee_ids:
            for i in range(len(weekends) - 1):
                sat1, sun1 = weekends[i]
                sat2, sun2 = weekends[i + 1]

                w1_free = ctx.model.new_bool_var(f"esw_w1_free_e{employee_id}_i{i}")
                w2_free = ctx.model.new_bool_var(f"esw_w2_free_e{employee_id}_i{i}")

                w1_sum = cp_model.LinearExpr.sum(vars_by_employee_date[(employee_id, sat1)] + vars_by_employee_date[(employee_id, sun1)])
                w2_sum = cp_model.LinearExpr.sum(vars_by_employee_date[(employee_id, sat2)] + vars_by_employee_date[(employee_id, sun2)])

                ctx.model.add(w1_sum == 0).only_enforce_if(w1_free)
                ctx.model.add(w1_sum >= 1).only_enforce_if(w1_free.Not())
                ctx.model.add(w2_sum == 0).only_enforce_if(w2_free)
                ctx.model.add(w2_sum >= 1).only_enforce_if(w2_free.Not())

                same_status = ctx.model.new_bool_var(f"esw_same_status_e{employee_id}_i{i}")
                ctx.model.add(same_status == 1).only_enforce_if([w1_free, w2_free])
                ctx.model.add(same_status == 1).only_enforce_if([w1_free.Not(), w2_free.Not()])
                ctx.model.add(same_status == 0).only_enforce_if([w1_free, w2_free.Not()])
                ctx.model.add(same_status == 0).only_enforce_if([w1_free.Not(), w2_free])
                penalties.append(same_status)

        total = ctx.model.new_int_var(0, len(penalties), "esw_total")
        ctx.model.add(total == cp_model.LinearExpr.sum(penalties))
        return (Penalty(objective_id=self.id, name="total", expression=total),)

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()