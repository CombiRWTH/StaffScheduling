from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Protocol

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext


@dataclass(frozen=True, slots=True)
class Penalty:
    """Raw penalty produced by one objective.

    The objective creates the expression. The model builder applies the global
    objective weight centrally so objectives do not read global configuration.
    """

    objective_id: str
    name: str
    expression: cp_model.LinearExpr
    multiplier: int = 1


class Objective(Protocol):
    """Soft CP-SAT model component.

    Objectives may add helper variables/constraints, but they return raw
    penalties. Global weights are applied centrally by the model builder.
    """

    id: ClassVar[str]

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]: ...

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]: ...


@dataclass(frozen=True, slots=True)
class WeightedPenalty:
    penalty: Penalty
    weight: int


def minimize_weighted_penalties(
    *,
    model: cp_model.CpModel,
    penalties: tuple[WeightedPenalty, ...],
) -> bool:
    if not penalties:
        return False

    model.minimize(sum(item.weight * item.penalty.multiplier * item.penalty.expression for item in penalties))
    return True
