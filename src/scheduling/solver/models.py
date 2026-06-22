from enum import StrEnum

from scheduling.domain import SchedulingBaseModel
from scheduling.domain.assignment import Assignment


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
    diagnostics: tuple[str, ...] = ()
