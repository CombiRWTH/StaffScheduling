from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class MinimizeOvertime:
    """
    Adds a penalty to the solver for including assigning overtime to employees.
    """

    id: ClassVar[str] = "minimize_overtime"

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        overtime: int = 0
        for account in ctx.dataset.monthly_work_accounts:
            employee_id = account.employee_id
            target_minutes = account.target_minutes
            actual_minutes = actual_minutes
            overtime += max(0, actual_minutes - target_minutes)

        total_overtime = ctx.model.new_int_var(
            0,
            overtime,
            "minimize_overtime__total_overtime"
        )

        ctx.model.add(total_overtime == overtime).with_name("minimize_overtime__define_total_overtime")

        return (
            Penalty(
                objective_id=self.id,
                name="total_overtime",
                expression=total_overtime,
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        return ()
