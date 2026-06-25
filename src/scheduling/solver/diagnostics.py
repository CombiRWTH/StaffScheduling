from enum import StrEnum

from scheduling.domain import SchedulingBaseModel


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SolverDiagnostic(SchedulingBaseModel):
    """Build/solve-time diagnostic.

    Diagnostics are not the same as post-solve audit findings. They describe
    model construction, infeasibility hints, configuration issues, or CP-SAT
    validation problems.
    """

    code: str
    severity: DiagnosticSeverity
    message: str
