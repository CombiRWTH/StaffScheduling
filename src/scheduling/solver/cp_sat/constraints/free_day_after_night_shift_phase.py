import datetime
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import SolverDiagnostic


class FreeDayAfterNightShiftPhase:
    """Ensure an employee has a free day after a night shift phase ends."""

    id: ClassVar[str] = "free_day_after_night_shift_phase"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        del params

        all_vars_by_emp_date, night_vars_by_emp_date = _group_vars(ctx)

        for (employee_id, date), night_vars_today in night_vars_by_emp_date.items():
            if not night_vars_today:
                continue

            tomorrow = date + datetime.timedelta(days=1)
            all_vars_tomorrow = all_vars_by_emp_date.get((employee_id, tomorrow), [])
            night_vars_tomorrow = night_vars_by_emp_date.get((employee_id, tomorrow), [])

            if not all_vars_tomorrow:
                continue

            works_night_today = ctx.model.new_bool_var(f"works_night_emp_{employee_id}_date_{date:%Y%m%d}")
            ctx.model.add_max_equality(works_night_today, night_vars_today)

            works_night_tomorrow = ctx.model.new_bool_var(f"works_night_emp_{employee_id}_date_{tomorrow:%Y%m%d}")
            if night_vars_tomorrow:
                ctx.model.add_max_equality(works_night_tomorrow, night_vars_tomorrow)
            else:
                ctx.model.add(works_night_tomorrow == 0)

            constraint = ctx.model.add(sum(all_vars_tomorrow) == 0)
            constraint.only_enforce_if([works_night_today, works_night_tomorrow.Not()])  # type: ignore
            constraint.with_name(_constraint_name(employee_id, tomorrow))

        return ()

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params

        findings: list[AuditFinding] = []
        actual_shifts = _group_actual_shifts(ctx)

        for (employee_id, date), shifts_today in actual_shifts.items():
            if not any(_is_night_shift(ctx, shift_id) for shift_id in shifts_today):
                continue

            tomorrow = date + datetime.timedelta(days=1)
            shifts_tomorrow = actual_shifts.get((employee_id, tomorrow), [])

            if not shifts_tomorrow:
                continue

            if not any(_is_night_shift(ctx, shift_id) for shift_id in shifts_tomorrow):
                findings.append(
                    AuditFinding(
                        code="free_day_after_night_shift_phase.violation",
                        severity=AuditSeverity.ERROR,
                        source_id=self.id,
                        message=(
                            f"Employee did not get a free day after a night shift phase ended. "
                            f"employee_id={employee_id} next_day={tomorrow.isoformat()}."
                        ),
                        date=tomorrow,
                    )
                )

        return tuple(findings)


# --- Helper Functions ---


def _constraint_name(employee_id: int, date_of_free_day: datetime.date) -> str:
    return f"free_day_after_night_shift__emp_{employee_id}__date_{date_of_free_day:%Y%m%d}"


# FIX: shift_id ist nun konsequent als `int` deklariert
def _is_night_shift(ctx: SolverContext | AuditContext, shift_id: int) -> bool:
    """
    Helper-Funktion zur Identifikation von Nachtschichten.
    """
    if hasattr(ctx, "is_night_shift"):
        return ctx.is_night_shift(shift_id)  # type: ignore

    return False


def _group_vars(
    ctx: SolverContext,
) -> tuple[
    dict[tuple[int, datetime.date], list[cp_model.IntVar]], dict[tuple[int, datetime.date], list[cp_model.IntVar]]
]:
    all_vars: defaultdict[tuple[int, datetime.date], list[cp_model.IntVar]] = defaultdict(list)
    night_vars: defaultdict[tuple[int, datetime.date], list[cp_model.IntVar]] = defaultdict(list)

    for key, variable in ctx.assignment_variables.items():
        employee_id, _, assignment_date, shift_id, _ = key

        all_vars[(employee_id, assignment_date)].append(variable)

        if _is_night_shift(ctx, shift_id):
            night_vars[(employee_id, assignment_date)].append(variable)

    return dict(all_vars), dict(night_vars)


# FIX: list[str] zu list[int] geändert, da shift_id ein int ist
def _group_actual_shifts(
    ctx: AuditContext,
) -> dict[tuple[int, datetime.date], list[int]]:
    actual_shifts: defaultdict[tuple[int, datetime.date], list[int]] = defaultdict(list)

    for assignment in ctx.assignments:
        actual_shifts[(assignment.employee_id, assignment.date)].append(assignment.shift_id)

    return dict(actual_shifts)
