from collections import defaultdict
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty

# Fridays (5) and Mondays (1) are the days adjacent to weekends
_NEAR_WEEKEND_DAYS = frozenset({1, 5})


class FreeDaysNearWeekend:
    """
    Rewards employees for being free on Fridays and Mondays (days adjacent to weekends).
    An additional bonus is given if the neighboring weekend day is also free,
    effectively rewarding a three-day weekend stretch.

    Weights: free near-weekend day = 1, free adjacent weekend day = 1,
             both free (bonus) = 4.
    Since this is a reward, the penalty is returned with multiplier=-1.
    """

    id: ClassVar[str] = "free_days_near_weekend"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        vars_by_employee_date: defaultdict[tuple[int, date], list[cp_model.IntVar]] = defaultdict(list)
        for (employee_id, _unit, d, _shift, _level), var in ctx.assignment_variables.items():
            vars_by_employee_date[(employee_id, d)].append(var)

        planning_dates_set = {key[2] for key in ctx.assignment_variables}
        employee_ids = {key[0] for key in ctx.assignment_variables}

        free_today_vars: list[cp_model.IntVar] = []
        free_adjacent_vars: list[cp_model.IntVar] = []
        free_both_vars: list[cp_model.IntVar] = []

        for employee_id in employee_ids:
            for d in sorted(planning_dates_set):
                if d.isoweekday() not in _NEAR_WEEKEND_DAYS:
                    continue

                today_vars = vars_by_employee_date[(employee_id, d)]

                # Reward: near-weekend day (Friday/Monday) is free
                free_today = ctx.model.new_bool_var(f"fdnw_free_today_e{employee_id}_d{d}")
                if today_vars:
                    ctx.model.add(sum(today_vars) == 0).only_enforce_if(free_today)
                    ctx.model.add(sum(today_vars) >= 1).only_enforce_if(free_today.Not())
                else:
                    ctx.model.add(free_today == 1)
                free_today_vars.append(free_today)

                # Adjacent weekend day: Saturday for Friday, Sunday for Monday
                adjacent = d + timedelta(days=1) if d.isoweekday() == 5 else d - timedelta(days=1)
                if adjacent not in planning_dates_set:
                    continue

                adjacent_vars = vars_by_employee_date[(employee_id, adjacent)]

                # Reward: the neighboring weekend day is also free
                free_adj = ctx.model.new_bool_var(f"fdnw_free_adj_e{employee_id}_d{d}")
                if adjacent_vars:
                    ctx.model.add(sum(adjacent_vars) == 0).only_enforce_if(free_adj)
                    ctx.model.add(sum(adjacent_vars) >= 1).only_enforce_if(free_adj.Not())
                else:
                    ctx.model.add(free_adj == 1)
                free_adjacent_vars.append(free_adj)

                # Bonus reward: both the near-weekend day and adjacent weekend day are free
                free_both = ctx.model.new_bool_var(f"fdnw_free_both_e{employee_id}_d{d}")
                ctx.model.add_bool_and([free_today, free_adj]).only_enforce_if(free_both)
                ctx.model.add_bool_or([free_today.Not(), free_adj.Not()]).only_enforce_if(free_both.Not())
                free_both_vars.append(free_both)

        if not free_today_vars:
            return ()

        max_total = len(free_today_vars) + len(free_adjacent_vars) + 4 * len(free_both_vars)
        total = ctx.model.new_int_var(0, max_total, "fdnw_total")
        ctx.model.add(total == sum(free_today_vars) + sum(free_adjacent_vars) + 4 * sum(free_both_vars))
        return (Penalty(objective_id=self.id, name="total", expression=total, multiplier=-1),)

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()
