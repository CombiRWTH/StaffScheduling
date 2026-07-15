from collections import defaultdict
from collections.abc import Mapping
from datetime import date
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.domain import WishType
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class FairPreferencesObjective:
    """Penalize repeatedly violating the same employee's free-time wishes."""

    id: ClassVar[str] = "fair_preferences"

    def add_to_model(self, ctx: SolverContext, params: Mapping[str, Any]) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        variables_by_employee_date: defaultdict[tuple[int, date], list[cp_model.IntVar]] = defaultdict(list)
        variables_by_employee_date_shift: defaultdict[tuple[int, date, int], list[cp_model.IntVar]] = defaultdict(list)

        for (employee_id, _unit_id, assignment_date, shift_id, _level), variable in ctx.assignment_variables.items():
            variables_by_employee_date[(employee_id, assignment_date)].append(variable)
            variables_by_employee_date_shift[(employee_id, assignment_date, shift_id)].append(variable)

        violations_by_employee: defaultdict[int, list[tuple[cp_model.IntVar, int]]] = defaultdict(list)
        for wish_index, wish in enumerate(ctx.dataset.wishes):
            if wish.type == WishType.FREE_DAY:
                assignment_variables = variables_by_employee_date[(wish.employee_id, wish.date)]
                strike_count = 3
            elif wish.type == WishType.FREE_SHIFT and wish.shift_id is not None:
                assignment_variables = variables_by_employee_date_shift[(wish.employee_id, wish.date, wish.shift_id)]
                strike_count = 1
            else:
                continue

            if not assignment_variables:
                continue

            violation = ctx.model.new_bool_var(f"fair_preferences__wish_{wish_index}__violated")
            ctx.model.add(sum(assignment_variables) >= 1).only_enforce_if(violation)
            ctx.model.add(sum(assignment_variables) == 0).only_enforce_if(violation.Not())
            violations_by_employee[wish.employee_id].append((violation, strike_count))

        penalties: list[Penalty] = []
        for employee_id, violations in violations_by_employee.items():
            max_strikes = sum(strike_count for _violation, strike_count in violations)
            total_strikes = sum(violation * strike_count for violation, strike_count in violations)
            tier_variables = [
                ctx.model.new_bool_var(f"fair_preferences__employee_{employee_id}__tier_{tier}")
                for tier in range(1, max_strikes + 1)
            ]
            ctx.model.add(sum(tier_variables) == total_strikes)

            penalties.append(
                Penalty(
                    objective_id=self.id,
                    name=f"employee_{employee_id}",
                    expression=sum(
                        tier**3 * tier_variable for tier, tier_variable in enumerate(tier_variables, start=1)
                    ),
                )
            )

        return tuple(penalties)

    def audit(self, ctx: AuditContext, params: Mapping[str, Any]) -> tuple[AuditFinding, ...]:
        return ()
