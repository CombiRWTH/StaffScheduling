import datetime
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding, AuditSeverity
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import SolverDiagnostic


class OneAssignmentPerDay:
    """Prevent more than one generated assignment per employee and day."""

    id: ClassVar[str] = "one_assignment_per_day"
    required: ClassVar[bool] = True

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]:
        del params

        vars_by_employee_date = _group_vars_by_employee_date(ctx)

        for (employee_id, assignment_date), variables in vars_by_employee_date.items():
            ctx.model.add(sum(variables) <= 1).with_name(_constraint_name(employee_id, assignment_date))

        return ()

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        del params

        findings: list[AuditFinding] = []
        actual_by_employee_date = _count_actual_assignments_by_employee_date(ctx)

        for (employee_id, assignment_date), count in actual_by_employee_date.items():
            if count <= 1:
                continue

            findings.append(
                AuditFinding(
                    code="one_assignment_per_day.violation",
                    severity=AuditSeverity.ERROR,
                    source_id=self.id,
                    message=(
                        f"Employee is assigned to multiple shifts on a single day. "
                        f"employee_id={employee_id} date={assignment_date.isoformat()} count={count}."
                    ),
                    date=assignment_date,
                )
            )

        return tuple(findings)


# --- Helper Functions ---


def _constraint_name(employee_id: int, date: datetime.date) -> str:
    return f"one_assignment_per_day__emp_{employee_id}__date_{date:%Y%m%d}"


def _group_vars_by_employee_date(
    ctx: SolverContext,
) -> dict[tuple[int, datetime.date], list[cp_model.IntVar]]:
    grouped: defaultdict[tuple[int, datetime.date], list[cp_model.IntVar]] = defaultdict(list)

    for key, variable in ctx.assignment_variables.items():
        employee_id, _, assignment_date, _, _ = key
        grouped[(employee_id, assignment_date)].append(variable)

    return dict(grouped)


def _count_actual_assignments_by_employee_date(
    ctx: AuditContext,
) -> dict[tuple[int, datetime.date], int]:
    actual: defaultdict[tuple[int, datetime.date], int] = defaultdict(int)

    for assignment in ctx.assignments:
        actual[(assignment.employee_id, assignment.date)] += 1

    return dict(actual)
