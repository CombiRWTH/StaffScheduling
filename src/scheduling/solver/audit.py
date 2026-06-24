from datetime import date as Date
from enum import StrEnum

from pydantic import Field

from scheduling.domain import SchedulingBaseModel


class AuditSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class AuditFinding(SchedulingBaseModel):
    """Post-solve finding about the generated schedule."""

    code: str
    severity: AuditSeverity
    message: str
    source_id: str
    planning_unit_id: int | None = None
    employee_id: int | None = None
    date: Date | None = None
    shift_id: int | None = None
    staff_level: str | None = None


class AuditReport(SchedulingBaseModel):
    findings: tuple[AuditFinding, ...] = Field(default_factory=tuple)
