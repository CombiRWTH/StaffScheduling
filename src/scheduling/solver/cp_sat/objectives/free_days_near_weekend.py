from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, timedelta
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty

type EmployeeDateKey = tuple[int, date]

_NEAR_WEEKEND_DAYS = frozenset({1, 5})


class FreeDaysNearWeekend:
    """Reward free days adjacent to weekends.

    Friday is paired with Saturday.
    Monday is paired with Sunday.

    Reward:
    - free Friday or Monday: 1
    - free adjacent weekend day: 1
    - both days free: additional 4

    The resulting expression is returned with multiplier -1 because the central
    objective minimizes penalties.
    """

    id: ClassVar[str] = "free_days_near_weekend"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        del params

        if not ctx.assignment_variables:
            return ()

        variables_by_employee_date: defaultdict[
            EmployeeDateKey,
            list[cp_model.IntVar],
        ] = defaultdict(list)

        for (
            employee_id,
            _planning_unit_id,
            assignment_date,
            _shift_id,
            _staff_level,
        ), variable in ctx.assignment_variables.items():
            variables_by_employee_date[(employee_id, assignment_date)].append(variable)

        planning_dates = self._planning_dates(ctx)
        planning_date_set = set(planning_dates)

        employee_ids = sorted(
            {
                employee_id
                for (
                    employee_id,
                    _planning_unit_id,
                    _assignment_date,
                    _shift_id,
                    _staff_level,
                ) in ctx.assignment_variables
            }
        )

        free_near_weekend_variables: list[cp_model.IntVar] = []
        free_adjacent_variables: list[cp_model.IntVar] = []
        free_both_variables: list[cp_model.IntVar] = []

        for employee_id in employee_ids:
            for current_date in planning_dates:
                if current_date.isoweekday() not in _NEAR_WEEKEND_DAYS:
                    continue

                adjacent_date = self._adjacent_weekend_date(current_date)

                if adjacent_date not in planning_date_set:
                    continue

                free_near_weekend = self._free_variable(
                    ctx,
                    variables_by_employee_date.get(
                        (employee_id, current_date),
                        [],
                    ),
                    name=(f"fdnw__free_near_e{employee_id}__d{current_date}"),
                )

                free_adjacent = self._free_variable(
                    ctx,
                    variables_by_employee_date.get(
                        (employee_id, adjacent_date),
                        [],
                    ),
                    name=(f"fdnw__free_adjacent_e{employee_id}__d{current_date}"),
                )

                free_both = ctx.model.new_bool_var(f"fdnw__free_both_e{employee_id}__d{current_date}")

                ctx.model.add_min_equality(
                    free_both,
                    [free_near_weekend, free_adjacent],
                )

                free_near_weekend_variables.append(free_near_weekend)
                free_adjacent_variables.append(free_adjacent)
                free_both_variables.append(free_both)

        if not free_near_weekend_variables:
            return ()

        maximum_reward = len(free_near_weekend_variables) + len(free_adjacent_variables) + 4 * len(free_both_variables)

        total_reward = ctx.model.new_int_var(
            0,
            maximum_reward,
            "fdnw__total_reward",
        )

        ctx.model.add(
            total_reward
            == sum(free_near_weekend_variables) + sum(free_adjacent_variables) + 4 * sum(free_both_variables)
        )

        return (
            Penalty(
                objective_id=self.id,
                name="total_reward",
                expression=total_reward,
                multiplier=-1,
            ),
        )

    @staticmethod
    def _free_variable(
        ctx: SolverContext, assignment_variables: Sequence[cp_model.IntVar], *, name: str
    ) -> cp_model.IntVar:
        worked = ctx.model.new_bool_var(f"{name}__worked")

        if assignment_variables:
            ctx.model.add_max_equality(
                worked,
                list(assignment_variables),
            )
        else:
            ctx.model.add(worked == 0)

        free = ctx.model.new_bool_var(name)
        ctx.model.add(free + worked == 1)

        return free

    @staticmethod
    def _adjacent_weekend_date(near_weekend_date: date) -> date:
        if near_weekend_date.isoweekday() == 5:
            return near_weekend_date + timedelta(days=1)

        return near_weekend_date - timedelta(days=1)

    @staticmethod
    def _planning_dates(ctx: SolverContext) -> tuple[date, ...]:
        dates: list[date] = []

        current_date = ctx.dataset.planning_month.start
        end_date = ctx.dataset.planning_month.end

        while current_date <= end_date:
            dates.append(current_date)
            current_date += timedelta(days=1)

        return tuple(dates)

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()
