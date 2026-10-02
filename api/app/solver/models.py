from enum import StrEnum
from typing import Literal, Self

from pydantic import model_validator

from app.domain import Assignment, Gap, RulePolicy, ScheduleCheck, SchedulingBaseModel
from app.solver.diagnostics import SolverDiagnostic


class SolutionStatus(StrEnum):
    """What CP-SAT found. OPTIMAL and FEASIBLE yield a candidate schedule; whether it is acceptable is
    the separate schedule check. INFEASIBLE is proven, UNKNOWN means neither a schedule nor a proof
    within the time limit, MODEL_INVALID a modelling error."""

    OPTIMAL = "optimal"
    FEASIBLE = "feasible"
    INFEASIBLE = "infeasible"
    MODEL_INVALID = "model_invalid"
    UNKNOWN = "unknown"


# The statuses that come with a candidate schedule.
FOUND = frozenset({SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE})


class RunConfiguration(SchedulingBaseModel):
    """The effective settings of one solve, recorded for reproduction."""

    policy: RulePolicy
    timeout_seconds: float
    """The total solver time of all stages."""
    search_workers: int | None
    random_seed: int | None


class StageReport(SchedulingBaseModel):
    """One objective tier's stage: the tier's value in the returned schedule and the bound CP-SAT proved.

    `value` equals the tier's field in the independent schedule check. OPTIMAL proves the value is the
    best possible after every higher tier; FEASIBLE means the stage's time ended first.
    """

    name: str
    status: Literal[SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE]
    value: int
    best_bound: float


class Solution(SchedulingBaseModel):
    status: SolutionStatus
    configuration: RunConfiguration
    wall_time_seconds: float
    assignments: tuple[Assignment, ...] = ()
    """Present only with a candidate schedule (OPTIMAL or FEASIBLE), like `gaps`, `stages` and `check`."""
    gaps: tuple[Gap, ...] = ()
    """The demand the schedule leaves unfilled; the check recomputes it from the assignments."""
    stages: tuple[StageReport, ...] = ()
    """Every objective tier in solving order. The status is OPTIMAL exactly when every stage is."""
    check: ScheduleCheck | None = None
    diagnostics: tuple[SolverDiagnostic, ...] = ()

    @property
    def found(self) -> bool:
        """Whether CP-SAT returned a candidate schedule."""
        return self.status in FOUND

    @model_validator(mode="after")
    def validate_schedule(self) -> Self:
        if self.found != (bool(self.stages) and self.check is not None):
            raise ValueError("A found schedule, and only a found one, has stages and a schedule check.")
        if self.found and (self.status == SolutionStatus.OPTIMAL) != all(
            stage.status == SolutionStatus.OPTIMAL for stage in self.stages
        ):
            raise ValueError("A solution is optimal exactly when every stage is.")
        if (self.assignments or self.gaps) and not self.found:
            raise ValueError("Only a found schedule has assignments and gaps.")
        if len({gap.demand_key for gap in self.gaps}) != len(self.gaps):
            raise ValueError("A demand row has at most one gap.")
        return self
