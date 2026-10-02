from enum import StrEnum

from app.domain import SchedulingBaseModel


class DiagnosticSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class SolverDiagnostic(SchedulingBaseModel):
    """Something the model build or solve noticed, such as a demand no candidate can cover.

    Diagnostics explain a solver result; whether a schedule holds the rules is the schedule check.
    """

    code: str
    severity: DiagnosticSeverity
    message: str
