"""The CP-SAT model of one planning month: every hard rule and the prioritized objective tiers.

`build_model` creates the candidate duties (`candidates.py`), adds each hard rule of
`constraints.HARD_RULES` and the tier expressions of `objectives.OBJECTIVES`, which the solver
optimizes one stage at a time. The rules are implemented here independently of the schedule check;
both share only the policy and the duty times.
"""

from dataclasses import dataclass

from ortools.sat.python import cp_model

from app.domain import Assignment, SchedulingDataset
from app.solver.diagnostics import SolverDiagnostic
from app.solver.model.candidates import CandidateModel, Expr
from app.solver.model.constraints import HARD_RULES
from app.solver.model.objectives import Tier, tier_objectives


@dataclass(frozen=True, slots=True)
class ScheduleModel:
    model: cp_model.CpModel
    candidates: dict[Assignment, cp_model.IntVar]
    # Every objective tier with its expression, highest priority first.
    tiers: tuple[tuple[Tier, Expr], ...]
    diagnostics: tuple[SolverDiagnostic, ...]

    def schedule(self, solver: cp_model.CpSolver) -> tuple[Assignment, ...]:
        """The candidate duties the solved model selects, sorted by date, station, shift and employee."""
        return tuple(
            sorted(
                (duty for duty, variable in self.candidates.items() if solver.value(variable)),
                key=lambda duty: (duty.date, duty.planning_unit_id, duty.shift_id, duty.employee_id),
            )
        )


def build_model(dataset: SchedulingDataset) -> ScheduleModel:
    """The month's complete model, without an objective; the solver sets one per stage."""
    model = CandidateModel(dataset)
    for rule in HARD_RULES:
        rule(model)
    tiers = tier_objectives(model)
    return ScheduleModel(model.cp, model.candidates, tiers, tuple(model.diagnostics))
