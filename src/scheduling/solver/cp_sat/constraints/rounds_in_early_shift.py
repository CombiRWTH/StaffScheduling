import datetime
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import DiagnosticSeverity, SolverDiagnostic


class RoundsInEarlyShift:
    """Ensure at least one employee qualified for 'rounds' is assigned to an early shift on weekdays."""

    id: ClassVar[str] = "rounds_in_early_shift"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        del params

        diagnostics: list[SolverDiagnostic] = []
        early_round_vars_by_date, active_weekdays = _group_vars(ctx)

        for date in active_weekdays:
            vars_for_date = early_round_vars_by_date.get(date, [])

            # Diagnostik: Wenn niemand Qualifiziertes an diesem Wochentag zur Verfügung steht,
            # warnen wir das System, anstatt eine Infeasible-Exception zu provozieren.
            if not vars_for_date:
                diagnostics.append(
                    SolverDiagnostic(
                        code="rounds_in_early_shift.no_candidates",
                        severity=DiagnosticSeverity.ERROR,
                        message=f"""No employees qualified for 'rounds' are
                        available for an early shift on {date.isoformat()}.""",
                    )
                )
                continue

            sum_expr = cp_model.LinearExpr.Sum(vars_for_date)  # type: ignore

            # Entkoppeltes Method-Chaining für Linter-Sicherheit
            constraint = ctx.model.add(sum_expr >= 1)
            constraint.with_name(_constraint_name(date))

        return tuple(diagnostics)

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params

        findings: list[AuditFinding] = []
        counts_by_date, active_weekdays = _group_actual_shifts(ctx)

        for date in active_weekdays:
            if counts_by_date.get(date, 0) == 0:
                findings.append(
                    AuditFinding(
                        code="rounds_in_early_shift.violation",
                        severity=AuditSeverity.ERROR,
                        source_id=self.id,
                        message=(
                            f"No employee qualified for 'rounds' is assigned to an early shift. "
                            f"date={date.isoformat()}."
                        ),
                        date=date,
                    )
                )

        return tuple(findings)


# --- Helper Functions ---


def _constraint_name(date: datetime.date) -> str:
    return f"rounds_in_early_shift__date_{date:%Y%m%d}"


def _is_early_shift(ctx: SolverContext | AuditContext, shift_id: int) -> bool:
    if hasattr(ctx, "is_early_shift"):
        return ctx.is_early_shift(shift_id)  # type: ignore
    return False


def _is_qualified_for_rounds(ctx: SolverContext | AuditContext, employee_id: int) -> bool:
    """
    Überprüft, ob die Person für die Visite ('rounds') qualifiziert ist.
    HINWEIS: Passen Sie die Zugriffslogik auf Ihren neuen `ctx.index` an.
    """
    # Variante A: Direkte Context-Methode
    if hasattr(ctx, "is_qualified_for_rounds"):
        return ctx.is_qualified_for_rounds(employee_id)  # type: ignore

    # Variante B: Zugriff über das Employee-Objekt im Index
    if hasattr(ctx, "index") and hasattr(ctx.index, "employees_by_id"):
        employee = ctx.index.employees_by_id.get(employee_id)
        if employee and hasattr(employee, "qualified"):
            return employee.capabilities(ROUNDS=True)  # type: ignore

    return False


def _group_vars(
    ctx: SolverContext,
) -> tuple[dict[datetime.date, list[cp_model.IntVar]], set[datetime.date]]:
    grouped: defaultdict[datetime.date, list[cp_model.IntVar]] = defaultdict(list)
    active_weekdays: set[datetime.date] = set()

    for key, variable in ctx.assignment_variables.items():
        employee_id, shift_id, assignment_date, _, _ = key

        # .isoweekday() gibt 1 (Montag) bis 7 (Sonntag) zurück
        if assignment_date.isoweekday() <= 5:
            active_weekdays.add(assignment_date)

            if _is_early_shift(ctx, shift_id) and _is_qualified_for_rounds(ctx, employee_id):
                grouped[assignment_date].append(variable)

    return dict(grouped), active_weekdays


def _group_actual_shifts(
    ctx: AuditContext,
) -> tuple[dict[datetime.date, int], set[datetime.date]]:
    counts: defaultdict[datetime.date, int] = defaultdict(int)
    active_weekdays: set[datetime.date] = set()

    for assignment in ctx.assignments:
        if assignment.date.isoweekday() <= 5:
            active_weekdays.add(assignment.date)

            if _is_early_shift(ctx, assignment.shift_id) and _is_qualified_for_rounds(ctx, assignment.employee_id):
                counts[assignment.date] += 1

    return dict(counts), active_weekdays
