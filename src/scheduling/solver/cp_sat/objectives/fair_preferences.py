from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.domain import WishType
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty

type EmployeeDateKey = tuple[int, date]
type EmployeeDateShiftKey = tuple[int, date, int]
type WeightedViolation = tuple[cp_model.IntVar, int]


class FairPreferencesObjective:
    """Penalize repeated wish violations increasingly per employee.

    Day-level wishes count as three strikes.
    Shift-specific wishes count as one strike.

    Violations are grouped by employee and wish category. Repeated violations
    become increasingly expensive through cubic penalty tiers.
    """

    id: ClassVar[str] = "fair_preferences"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        del params

        if not ctx.assignment_variables:
            return ()

        variables_by_employee_date: defaultdict[EmployeeDateKey, list[cp_model.IntVar]] = defaultdict(list)

        variables_by_employee_date_shift: defaultdict[EmployeeDateShiftKey, list[cp_model.IntVar]] = defaultdict(list)

        for (
            employee_id,
            _planning_unit_id,
            assignment_date,
            shift_id,
            _staff_level,
        ), variable in ctx.assignment_variables.items():
            variables_by_employee_date[(employee_id, assignment_date)].append(variable)

            variables_by_employee_date_shift[(employee_id, assignment_date, shift_id)].append(variable)

        free_wish_violations = self._free_wish_violations(
            ctx,
            variables_by_employee_date=variables_by_employee_date,
            variables_by_employee_date_shift=variables_by_employee_date_shift,
        )

        preferred_wish_violations = self._preferred_wish_violations(
            ctx,
            variables_by_employee_date=variables_by_employee_date,
            variables_by_employee_date_shift=variables_by_employee_date_shift,
        )

        free_wish_penalties = self._bucketed_penalties(
            ctx,
            free_wish_violations,
            wish_group="free",
        )

        preferred_wish_penalties = self._bucketed_penalties(
            ctx,
            preferred_wish_violations,
            wish_group="preferred",
        )

        return free_wish_penalties + preferred_wish_penalties

    def _free_wish_violations(
        self,
        ctx: SolverContext,
        *,
        variables_by_employee_date: Mapping[EmployeeDateKey, list[cp_model.IntVar]],
        variables_by_employee_date_shift: Mapping[EmployeeDateShiftKey, list[cp_model.IntVar]],
    ) -> dict[int, list[WeightedViolation]]:
        violations_by_employee: defaultdict[int, list[WeightedViolation]] = defaultdict(list)

        for wish_index, wish in enumerate(ctx.dataset.wishes):
            assignment_variables: list[cp_model.IntVar]
            strike_count: int

            if wish.type == WishType.FREE_DAY:
                assignment_variables = variables_by_employee_date.get(
                    (wish.employee_id, wish.date),
                    [],
                )
                strike_count = 3
            elif wish.type == WishType.FREE_SHIFT and wish.shift_id is not None:
                assignment_variables = variables_by_employee_date_shift.get(
                    (
                        wish.employee_id,
                        wish.date,
                        wish.shift_id,
                    ),
                    [],
                )
                strike_count = 1
            else:
                continue

            if not assignment_variables:
                continue

            violation = self._worked_variable(
                ctx,
                assignment_variables,
                name=(f"fair_preferences__free_wish_{wish_index}__violated"),
            )

            violations_by_employee[wish.employee_id].append((violation, strike_count))

        return dict(violations_by_employee)

    def _preferred_wish_violations(
        self,
        ctx: SolverContext,
        *,
        variables_by_employee_date: Mapping[EmployeeDateKey, list[cp_model.IntVar]],
        variables_by_employee_date_shift: Mapping[EmployeeDateShiftKey, list[cp_model.IntVar]],
    ) -> dict[int, list[WeightedViolation]]:
        violations_by_employee: defaultdict[int, list[WeightedViolation]] = defaultdict(list)

        for wish_index, wish in enumerate(ctx.dataset.wishes):
            assignment_variables: list[cp_model.IntVar]
            strike_count: int

            if wish.type == WishType.PREFERRED_DAY:
                assignment_variables = variables_by_employee_date.get(
                    (wish.employee_id, wish.date),
                    [],
                )
                strike_count = 3
            elif wish.type == WishType.PREFERRED_SHIFT and wish.shift_id is not None:
                assignment_variables = variables_by_employee_date_shift.get(
                    (
                        wish.employee_id,
                        wish.date,
                        wish.shift_id,
                    ),
                    [],
                )
                strike_count = 1
            else:
                continue

            if not assignment_variables:
                continue

            fulfilled = self._worked_variable(
                ctx,
                assignment_variables,
                name=(f"fair_preferences__preferred_wish_{wish_index}__fulfilled"),
            )

            violation = ctx.model.new_bool_var(f"fair_preferences__preferred_wish_{wish_index}__violated")

            ctx.model.add(violation + fulfilled == 1)

            violations_by_employee[wish.employee_id].append((violation, strike_count))

        return dict(violations_by_employee)

    def _bucketed_penalties(
        self,
        ctx: SolverContext,
        violations_by_employee: Mapping[int, list[WeightedViolation]],
        *,
        wish_group: str,
    ) -> tuple[Penalty, ...]:
        penalties: list[Penalty] = []

        for employee_id, violations in violations_by_employee.items():
            maximum_strikes = sum(strike_count for _violation, strike_count in violations)

            if maximum_strikes == 0:
                continue

            total_strikes = ctx.model.new_int_var(
                0,
                maximum_strikes,
                (f"fair_preferences__{wish_group}__employee_{employee_id}__total_strikes"),
            )

            weighted_violations = [violation * strike_count for violation, strike_count in violations]

            weighted_violation_sum = self._sum_linear_expressions(weighted_violations)

            ctx.model.add(total_strikes == weighted_violation_sum)

            tier_variables = [
                ctx.model.new_bool_var(f"fair_preferences__{wish_group}__employee_{employee_id}__tier_{tier}")
                for tier in range(1, maximum_strikes + 1)
            ]

            ctx.model.add(sum(tier_variables) == total_strikes)

            for lower_tier, higher_tier in zip(
                tier_variables,
                tier_variables[1:],
                strict=False,
            ):
                ctx.model.add(lower_tier >= higher_tier)

            tier_cost_expressions = [
                tier**3 * tier_variable
                for tier, tier_variable in enumerate(
                    tier_variables,
                    start=1,
                )
            ]

            tier_cost_sum = self._sum_linear_expressions(tier_cost_expressions)

            maximum_tier_cost = sum(tier**3 for tier in range(1, maximum_strikes + 1))

            total_tier_cost = ctx.model.new_int_var(
                0,
                maximum_tier_cost,
                (f"fair_preferences__{wish_group}__employee_{employee_id}__total_tier_cost"),
            )

            ctx.model.add(total_tier_cost == tier_cost_sum)

            penalties.append(
                Penalty(
                    objective_id=self.id,
                    name=(f"employee_{employee_id}__{wish_group}_wishes"),
                    expression=total_tier_cost,
                )
            )

        return tuple(penalties)

    @staticmethod
    def _worked_variable(
        ctx: SolverContext, assignment_variables: Sequence[cp_model.IntVar], *, name: str
    ) -> cp_model.IntVar:
        worked = ctx.model.new_bool_var(name)
        ctx.model.add_max_equality(
            worked,
            list(assignment_variables),
        )
        return worked

    @staticmethod
    def _sum_linear_expressions(expressions: Sequence[cp_model.LinearExpr]) -> cp_model.LinearExpr:
        if not expressions:
            raise ValueError("At least one linear expression is required.")

        total = expressions[0]

        for expression in expressions[1:]:
            total += expression

        return total

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()
