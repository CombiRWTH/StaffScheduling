import datetime
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import SolverDiagnostic

# Angenommen, Ihre Enum/Models sind importierbar, andernfalls als Typ-Hinweise nutzen
# from scheduling.domain.availability import Availability, AvailabilityType


class EmployeeAvailabilities:
    """Ensure employees do not work on dates or shifts they are unavailable for.

    Also prevents night shifts from spilling over into full-day absences (e.g., vacations).
    """

    id: ClassVar[str] = "employee_availabilities"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        del params

        blocked_days, allowed_shifts_for_day = _parse_availabilities(ctx)

        for key, variable in ctx.assignment_variables.items():
            employee_id, shift_id, date, _, _ = key

            # Regel 1: Voller Abwesenheitstag (Urlaub, Training, etc.)
            if (employee_id, date) in blocked_days:
                ctx.model.add(variable == 0).with_name(
                    f"avail_blocked_full__emp_{employee_id}_date_{date:%Y%m%d}_shift_{shift_id}"
                )
                continue

            # Regel 2: Partielle Verfügbarkeit (AVAILABLE_ONLY)
            if (employee_id, date) in allowed_shifts_for_day:
                if shift_id not in allowed_shifts_for_day[(employee_id, date)]:
                    ctx.model.add(variable == 0).with_name(
                        f"avail_blocked_partial__emp_{employee_id}_date_{date:%Y%m%d}_shift_{shift_id}"
                    )
                    continue

            # Regel 3: Spillover-Prävention (Nachtschicht vor einem vollen Abwesenheitstag)
            if _is_night_shift(ctx, shift_id):
                tomorrow = date + datetime.timedelta(days=1)
                if (employee_id, tomorrow) in blocked_days:
                    ctx.model.add(variable == 0).with_name(
                        f"avail_blocked_spillover__emp_{employee_id}_date_{date:%Y%m%d}_shift_{shift_id}"
                    )

        return ()

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params

        findings: list[AuditFinding] = []
        blocked_days, allowed_shifts_for_day = _parse_availabilities(ctx)

        for assignment in ctx.assignments:
            # Type-Guards (Nur relevante Zuweisungen prüfen)
            if assignment.employee_id is None or assignment.shift_id is None or assignment.date is None:  # type: ignore
                continue

            emp_id = assignment.employee_id
            shift_id = assignment.shift_id
            date = assignment.date

            # Audit 1: Zuweisung an einem voll blockierten Tag
            if (emp_id, date) in blocked_days:
                findings.append(
                    AuditFinding(
                        code="employee_availabilities.violation_full_day",
                        severity=AuditSeverity.ERROR,
                        source_id=self.id,
                        message=(
                            f"Employee is assigned to a shift on a fully blocked day. "
                            f"employee_id={emp_id} date={date.isoformat()} shift_id={shift_id}."
                        ),
                        date=date,
                    )
                )

            # Audit 2: Zuweisung einer unzulässigen Schicht (AVAILABLE_ONLY)
            elif (emp_id, date) in allowed_shifts_for_day and shift_id not in allowed_shifts_for_day[(emp_id, date)]:
                findings.append(
                    AuditFinding(
                        code="employee_availabilities.violation_partial_day",
                        severity=AuditSeverity.ERROR,
                        source_id=self.id,
                        message=(
                            f"Employee is assigned to a restricted shift type. "
                            f"employee_id={emp_id} date={date.isoformat()} shift_id={shift_id}."
                        ),
                        date=date,
                    )
                )

            # Audit 3: Unzulässiger Spillover (Nachtschicht am Vortag)
            elif _is_night_shift(ctx, shift_id):
                tomorrow = date + datetime.timedelta(days=1)
                if (emp_id, tomorrow) in blocked_days:
                    findings.append(
                        AuditFinding(
                            code="employee_availabilities.violation_spillover",
                            severity=AuditSeverity.ERROR,
                            source_id=self.id,
                            message=(
                                f"Employee is assigned to a night shift spilling over into a blocked day. "
                                f"employee_id={emp_id} date={date.isoformat()} shift_id={shift_id}."
                            ),
                            date=tomorrow,  # Das Datum des Regelbruchs ist der blockierte Tag
                        )
                    )

        return tuple(findings)


# --- Helper Functions ---


def _parse_availabilities(
    ctx: SolverContext | AuditContext,
) -> tuple[set[tuple[int, datetime.date]], dict[tuple[int, datetime.date], set[int]]]:
    """
    Parses the new Availability Pydantic models into O(1) lookup structures.
    """
    blocked_days: set[tuple[int, datetime.date]] = set()
    allowed_shifts: defaultdict[tuple[int, datetime.date], set[int]] = defaultdict(set)

    # Annahme: Availabilities sind Teil des Contexts oder Index
    # (Passen Sie den Attributnamen ctx.availabilities entsprechend Ihrer Struktur an)
    availabilities = getattr(ctx, "availabilities", [])

    # Alternativer Fallback, falls sie im Index liegen:
    # availabilities = getattr(ctx.index, "availabilities", []) if hasattr(ctx, "index") else availabilities

    for avail in availabilities:
        # Hier nutzen wir das Enum als String, um Abhängigkeiten gering zu halten
        if str(avail.availability_type) == "available_only":
            if avail.shift_ids:
                allowed_shifts[(avail.employee_id, avail.date)].update(avail.shift_ids)
        else:
            blocked_days.add((avail.employee_id, avail.date))

    return blocked_days, dict(allowed_shifts)


def _is_night_shift(ctx: SolverContext | AuditContext, shift_id: int) -> bool:
    """Checks if the shift spills over into the next day."""
    if hasattr(ctx, "is_night_shift"):
        return ctx.is_night_shift(shift_id)  # type: ignore
    return False
