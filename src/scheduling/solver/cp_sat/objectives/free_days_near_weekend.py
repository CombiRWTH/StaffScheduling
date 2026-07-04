from collections import defaultdict
from collections.abc import Mapping
from datetime import date, timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty

# Weekdays adjacent to a weekend.
# ISO weekday: Monday = 1, Friday = 5
_NEAR_WEEKEND_DAYS = frozenset({1, 5})


class FreeDaysNearWeekend:
    """
    Rewards employees for having free days adjacent to a weekend.

    A free Friday or Monday is rewarded.
    An additional reward is given if the adjacent weekend day is also free.
    """

    id: ClassVar[str] = "free_days_near_weekend"

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        # Group assignment variables by employee and date.
        vars_by_employee_date: defaultdict[
            tuple[int, date],
            list[cp_model.IntVar],
        ] = defaultdict(list)

        for (employee_id, _, assignment_date, _, _), variable in ctx.assignment_variables.items():
            vars_by_employee_date[(employee_id, assignment_date)].append(variable)

        # Build planning dates from the planning month.
        planning_dates: list[date] = []

        current_date = ctx.dataset.planning_month.start
        while current_date <= ctx.dataset.planning_month.end:
            planning_dates.append(current_date)
            current_date += timedelta(days=1)

        planning_dates_set = set(planning_dates)

        employee_ids = {
            key[0]
            for key in ctx.assignment_variables.keys()
        }

        reward_variables: list[cp_model.IntVar] = []
        reward_weights: list[int] = []

        for employee_id in employee_ids:
            for current_date in planning_dates:

                if current_date.isoweekday() not in _NEAR_WEEKEND_DAYS:
                    continue

                adjacent_date = (
                    current_date + timedelta(days=1)
                    if current_date.isoweekday() == 5
                    else current_date - timedelta(days=1)
                )

                if adjacent_date not in planning_dates_set:
                    continue

                today_assignment_vars = vars_by_employee_date[(employee_id, current_date)]
                adjacent_assignment_vars = vars_by_employee_date[(employee_id, adjacent_date)]

                free_today = ctx.model.new_bool_var(
                    f"free_today_e{employee_id}_{current_date}"
                )

                ctx.model.add(
                    cp_model.LinearExpr.sum(today_assignment_vars) == 0
                ).only_enforce_if(free_today)

                ctx.model.add(
                    cp_model.LinearExpr.sum(today_assignment_vars) >= 1
                ).only_enforce_if(free_today.Not())

                free_adjacent = ctx.model.new_bool_var(
                    f"free_adjacent_e{employee_id}_{current_date}"
                )

                ctx.model.add(
                    cp_model.LinearExpr.sum(adjacent_assignment_vars) == 0
                ).only_enforce_if(free_adjacent)

                ctx.model.add(
                    cp_model.LinearExpr.sum(adjacent_assignment_vars) >= 1
                ).only_enforce_if(free_adjacent.Not())

                free_both = ctx.model.new_bool_var(
                    f"free_both_e{employee_id}_{current_date}"
                )

                ctx.model.add_bool_and(
                    [free_today, free_adjacent]
                ).only_enforce_if(free_both)

                ctx.model.add_bool_or(
                    [free_today.Not(), free_adjacent.Not()]
                ).only_enforce_if(free_both.Not())

                reward_variables.extend(
                    [
                        free_today,
                        free_adjacent,
                        free_both,
                    ]
                )

                reward_weights.extend(
                    [
                        1,
                        1,
                        4,
                    ]
                )

        if not reward_variables:
            return ()

        total_reward = ctx.model.new_int_var(
            0,
            sum(reward_weights),
            "free_days_near_weekend__total_reward",
        )

        ctx.model.add(
            total_reward
            == cp_model.LinearExpr.weighted_sum(
                reward_variables,
                reward_weights,
            )
        ).with_name(
            "free_days_near_weekend__define_total_reward"
        )

        return (
            Penalty(
                objective_id=self.id,
                name="total_reward",
                expression=total_reward,
                multiplier=-1,
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        return ()
