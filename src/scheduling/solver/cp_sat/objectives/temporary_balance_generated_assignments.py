from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class TemporaryBalanceGeneratedAssignments:
    """Temporary migration objective.

    This is intentionally named as temporary. It should be deleted once the real
    target-working-time objective exists.
    """

    id: ClassVar[str] = "temporary_balance_generated_assignments"

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        variables_by_employee: defaultdict[int, list[cp_model.IntVar]] = defaultdict(list)

        for key, variable in ctx.assignment_variables.items():
            employee_id, _, _, _, _ = key
            variables_by_employee[employee_id].append(variable)

        generated_counts = [sum(variables) for variables in variables_by_employee.values()]

        max_generated_assignments = ctx.model.new_int_var(
            0,
            len(ctx.assignment_variables),
            "temporary_balance_generated_assignments__max_per_employee",
        )

        ctx.model.add_max_equality(
            max_generated_assignments,
            generated_counts,
        ).with_name("temporary_balance_generated_assignments__define_max_per_employee")

        return (
            Penalty(
                objective_id=self.id,
                name="max_generated_assignments_per_employee",
                expression=max_generated_assignments,
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        return ()
