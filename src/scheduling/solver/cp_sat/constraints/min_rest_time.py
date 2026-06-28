import datetime
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import SolverDiagnostic


class MinimumRestTime:
    """Ensure an employee has a minimum rest time between shifts.

    Specifically prevents a Late shift from being immediately followed by an Early shift on the next day.
    """

    id: ClassVar[str] = "minimum_rest_time"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        del params

        late_vars_by_emp_date, early_vars_by_emp_date = _group_vars(ctx)

        for (employee_id, date), late_vars_today in late_vars_by_emp_date.items():
            if not late_vars_today:
                continue

            tomorrow = date + datetime.timedelta(days=1)
            early_vars_tomorrow = early_vars_by_emp_date.get((employee_id, tomorrow), [])

            if not early_vars_tomorrow:
                continue

            # # OR-Tools native Summenbildung (mit Ignorieren der unvollständigen OR-Tools-Stubs)
            sum_late = cp_model.LinearExpr.Sum(late_vars_today)  # type: ignore
            sum_early = cp_model.LinearExpr.Sum(early_vars_tomorrow)  # type: ignore

            # Entkoppeltes Method-Chaining zur Vermeidung von Linter-Warnungen
            constraint = ctx.model.add(sum_late + sum_early <= 1)
            constraint.with_name(_constraint_name(employee_id, date))

        return ()

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params

        findings: list[AuditFinding] = []
        late_shifts_actual, early_shifts_actual = _group_actual_shifts(ctx)

        for employee_id, date in late_shifts_actual:
            tomorrow = date + datetime.timedelta(days=1)

            # Ein simpler Lookup im Set ($O(1)$) reicht aus
            if (employee_id, tomorrow) in early_shifts_actual:
                findings.append(
                    AuditFinding(
                        code="minimum_rest_time.violation",
                        severity=AuditSeverity.ERROR,
                        source_id=self.id,
                        message=(
                            f"Minimum rest time violated. Late shift followed by an Early shift. "
                            f"employee_id={employee_id} late_date={date.isoformat()} early_date={tomorrow.isoformat()}."
                        ),
                        date=tomorrow,  # Das Datum der Regelverletzung ist der Tag der unzulässigen Frühschicht
                    )
                )

        return tuple(findings)


# --- Helper Functions ---


def _constraint_name(employee_id: int, late_shift_date: datetime.date) -> str:
    return f"min_rest_time__emp_{employee_id}__date_{late_shift_date:%Y%m%d}"


def _is_late_shift(ctx: SolverContext | AuditContext, shift_id: int) -> bool:
    if hasattr(ctx, "is_late_shift"):
        return ctx.is_late_shift(shift_id)  # type: ignore
    return False


def _is_early_shift(ctx: SolverContext | AuditContext, shift_id: int) -> bool:
    if hasattr(ctx, "is_early_shift"):
        return ctx.is_early_shift(shift_id)  # type: ignore
    return False


def _group_vars(
    ctx: SolverContext,
) -> tuple[
    dict[tuple[int, datetime.date], list[cp_model.IntVar]], dict[tuple[int, datetime.date], list[cp_model.IntVar]]
]:
    late_vars: defaultdict[tuple[int, datetime.date], list[cp_model.IntVar]] = defaultdict(list)
    early_vars: defaultdict[tuple[int, datetime.date], list[cp_model.IntVar]] = defaultdict(list)

    for key, variable in ctx.assignment_variables.items():
        employee_id, shift_id, assignment_date, _, _ = key

        if _is_late_shift(ctx, shift_id):
            late_vars[(employee_id, assignment_date)].append(variable)
        elif _is_early_shift(ctx, shift_id):
            early_vars[(employee_id, assignment_date)].append(variable)

    return dict(late_vars), dict(early_vars)


def _group_actual_shifts(
    ctx: AuditContext,
) -> tuple[set[tuple[int, datetime.date]], set[tuple[int, datetime.date]]]:
    # Sets sind performanter als Dicts, da wir nicht iterieren oder zählen müssen,
    # sondern nur prüfen: "Gab es an diesem Tag diesen Schichttyp?"
    late_shifts: set[tuple[int, datetime.date]] = set()
    early_shifts: set[tuple[int, datetime.date]] = set()

    for assignment in ctx.assignments:
        if _is_late_shift(ctx, assignment.shift_id):
            late_shifts.add((assignment.employee_id, assignment.date))
        elif _is_early_shift(ctx, assignment.shift_id):
            early_shifts.add((assignment.employee_id, assignment.date))

    return late_shifts, early_shifts
