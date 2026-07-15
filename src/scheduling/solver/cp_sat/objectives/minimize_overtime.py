from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class MinimizeOvertime:
    """
    Adds a penalty to the solver for assigning overtime to employees.
    Mathematical formulation: sum(max(0, planned_work + actual_work - target_work))
    """

    id: ClassVar[str] = "minimize_overtime"

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        accounts = {acc.employee_id: acc for acc in ctx.dataset.monthly_work_accounts}
        exprs_by_employee = _group_weighted_vars(ctx)

        overtime_vars: list[cp_model.IntVar] = []

        for employee_id, expressions in exprs_by_employee.items():
            account = accounts.get(employee_id)
            if not account:
                continue

            actual_worked = account.actual_minutes or 0
            target_minutes = account.target_minutes

            # W_i: Summe der zu planenden Schichten
            total_work_expr = cp_model.LinearExpr.Sum(expressions)  # type: ignore

            # O_i: Überstunden-Variable für den jeweiligen Mitarbeiter
            # Upper Bound: 44640 (31 Tage * 24h * 60m) fungiert als sicheres Maximum für einen Monat
            emp_overtime_var = ctx.model.new_int_var(0, 44640, f"minimize_overtime__emp_{employee_id}")

            # Constraint: O_i >= W_i + A_i - T_i
            ctx.model.add(emp_overtime_var >= total_work_expr + actual_worked - target_minutes).with_name(
                f"minimize_overtime__bound_emp_{employee_id}"
            )

            overtime_vars.append(emp_overtime_var)

        if not overtime_vars:
            return ()

        return (
            Penalty(
                objective_id=self.id,
                name="total_overtime",
                expression=cp_model.LinearExpr.Sum(overtime_vars),  # type: ignore
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        # Objectives produzieren primär keine Audit-Findings (im Gegensatz zu Constraints).
        # Falls gewünscht, kann hier die kumulierte Überstunden-Metrik berechnet werden.
        return ()


def _group_weighted_vars(ctx: SolverContext) -> dict[int, list[cp_model.LinearExpr]]:
    exprs: defaultdict[int, list[cp_model.LinearExpr]] = defaultdict(list)

    # Mapping für schnellen Zugriff auf Schichtdauern
    shift_durations = {s.shift_id: (s.end_minute - s.start_minute) for s in ctx.dataset.shifts}

    for key, variable in ctx.assignment_variables.items():
        employee_id, _, _, shift_id, _ = key

        # Falls Schicht nicht im Dataset, Dauer 0
        duration = shift_durations.get(shift_id, 0)
        exprs[employee_id].append(variable * duration)

    return dict(exprs)
