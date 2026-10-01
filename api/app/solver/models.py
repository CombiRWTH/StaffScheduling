from enum import StrEnum

from pydantic import Field

from app.domain import SchedulingBaseModel
from app.domain.assignment import Assignment
from app.solver.audit import AuditReport
from app.solver.diagnostics import SolverDiagnostic


class SolutionStatus(StrEnum):
    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    MODEL_INVALID = "model_invalid"
    UNKNOWN = "unknown"
    ERROR = "error"


class Solution(SchedulingBaseModel):
    status: SolutionStatus
    assignments: tuple[Assignment, ...] = ()
    diagnostics: tuple[SolverDiagnostic, ...] = ()
    audit: AuditReport = Field(default_factory=AuditReport)
