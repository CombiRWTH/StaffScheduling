from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import SolverDiagnostic
from scheduling.timeoffice import facts


class TargetWorkingTime:
    """Ensure each employee works their target monthly amount of time."""

    id: ClassVar[str] = "target_working_time"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        # Parameter aus params mit Fallbacks
        tolerance_less = facts.TIMEOFFICE_FACTS.target_working_time_tolerance_less
        tolerance_more = facts.TIMEOFFICE_FACTS.target_working_time_tolerance_more

        # Mapping von employee_id auf MonthlyWorkAccount
        accounts = {acc.employee_id: acc for acc in ctx.dataset.monthly_work_accounts}

        # Gruppen der gewichteten Variablen (Schichtdauer) pro Mitarbeiter
        exprs_by_employee = _group_weighted_vars(ctx)

        for employee_id, expressions in exprs_by_employee.items():
            account = accounts.get(employee_id)
            if not account:
                continue

            # Zielvorgabe: Target minus bereits geleistete Zeit
            actual_worked = account.actual_minutes or 0
            target_net = max(account.target_minutes - actual_worked, 0)

            # Summe der zu planenden Schichten
            total_work_expr = cp_model.LinearExpr.Sum(expressions)  # type: ignore

            # Constraints hinzufügen
            upper_limit = target_net + tolerance_more
            lower_limit = target_net - tolerance_less

            ctx.model.add(total_work_expr <= upper_limit).with_name(f"target_work_upper__emp_{employee_id}")
            ctx.model.add(total_work_expr >= lower_limit).with_name(f"target_work_lower__emp_{employee_id}")

        return ()

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        tolerance_less = facts.TIMEOFFICE_FACTS.target_working_time_tolerance_less
        tolerance_more = facts.TIMEOFFICE_FACTS.target_working_time_tolerance_more

        findings: list[AuditFinding] = []
        accounts = {acc.employee_id: acc for acc in ctx.dataset.monthly_work_accounts}

        # Historische Zuweisungen aus dem Audit-Kontext
        actual_durations = _group_actual_durations(ctx)

        for employee_id, total_worked in actual_durations.items():
            account = accounts.get(employee_id)
            if not account:
                continue

            target_net = max(account.target_minutes - (account.actual_minutes or 0), 0)

            upper_limit = target_net + tolerance_more
            lower_limit = target_net - tolerance_less

            if total_worked > upper_limit:
                findings.append(_create_finding(self.id, employee_id, total_worked, target_net, upper_limit, "upper"))
            elif total_worked < lower_limit:
                findings.append(_create_finding(self.id, employee_id, total_worked, target_net, lower_limit, "lower"))

        return tuple(findings)


# --- Helper Functions ---


def _create_finding(source_id: str, employee_id: int, actual: int, target: int, limit: int, bound: str) -> AuditFinding:
    return AuditFinding(
        code=f"target_working_time.violation_{bound}",
        severity=AuditSeverity.ERROR,
        source_id=source_id,
        message=(
            f"Employee working time violates {bound} limit. "
            f"employee_id={employee_id} actual_minutes={actual} target_minutes={target} limit={limit}."
        ),
        date=None,
    )


def _group_weighted_vars(ctx: SolverContext) -> dict[int, list[cp_model.LinearExpr]]:
    exprs: defaultdict[int, list[cp_model.LinearExpr]] = defaultdict(list)

    # Mapping für schnellen Zugriff auf Schichtdauern
    shift_durations = {s.shift_id: (s.end_minute - s.start_minute) for s in ctx.dataset.shifts}

    for key, variable in ctx.assignment_variables.items():
        employee_id, _, _, shift_id, _ = key

        # Falls Schicht nicht in Dataset (sollte nicht passieren), Dauer 0
        duration = shift_durations.get(shift_id, 0)
        exprs[employee_id].append(variable * duration)

    return dict(exprs)


def _group_actual_durations(ctx: AuditContext) -> dict[int, int]:
    durations: defaultdict[int, int] = defaultdict(int)
    shift_durations = {s.shift_id: (s.end_minute - s.start_minute) for s in ctx.dataset.shifts}

    for assignment in ctx.assignments:
        # Pydantic Modelle garantieren die Existenz
        if assignment.employee_id is not None and assignment.shift_id is not None:  # type: ignore
            durations[assignment.employee_id] += shift_durations.get(assignment.shift_id, 0)

    return dict(durations)
