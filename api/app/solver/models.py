from enum import StrEnum

from pydantic import computed_field

from app.domain import Assignment, RulePolicy, ScheduleCheck, SchedulingBaseModel
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


class ObjectiveWeights(SchedulingBaseModel):
    """Dominance coefficients of the three objective tiers, derived from the input's bounds.

    One unit of a higher tier outweighs any possible change of all lower tiers together.
    """

    health_events: int
    balance_deviation_minutes: int
    surplus_intermediate_duties: int


class RunConfiguration(SchedulingBaseModel):
    """The effective settings of one solve, recorded for reproduction."""

    policy: RulePolicy
    weights: ObjectiveWeights
    timeout_seconds: float
    search_workers: int | None
    random_seed: int | None


class ObjectiveReport(SchedulingBaseModel):
    """CP-SAT's objective of the returned schedule and the best bound it proved.

    `value` equals the weighted total of the independently computed scores in the schedule check;
    a time-limited FEASIBLE schedule can be improved by up to the gap.
    """

    value: int
    best_bound: float

    @computed_field
    @property
    def relative_gap(self) -> float:
        return abs(self.value - self.best_bound) / max(1.0, abs(self.value))


class Solution(SchedulingBaseModel):
    status: SolutionStatus
    configuration: RunConfiguration
    wall_time_seconds: float
    # Present only with a candidate schedule (OPTIMAL or FEASIBLE).
    assignments: tuple[Assignment, ...] = ()
    objective: ObjectiveReport | None = None
    check: ScheduleCheck | None = None
    diagnostics: tuple[SolverDiagnostic, ...] = ()
