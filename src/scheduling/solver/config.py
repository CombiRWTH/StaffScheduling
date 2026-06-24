from typing import Any

from pydantic import Field

from scheduling.domain import SchedulingBaseModel
from scheduling.solver.cp_sat.constraints.minimum_staffing import MinimumStaffing
from scheduling.solver.cp_sat.objectives.temporary_balance_generated_assignments import (
    TemporaryBalanceGeneratedAssignments,
)


class ConstraintConfig(SchedulingBaseModel):
    enabled: bool
    params: dict[str, Any] = Field(default_factory=dict)


class ObjectiveConfig(SchedulingBaseModel):
    enabled: bool
    weight: int
    params: dict[str, Any] = Field(default_factory=dict)


class SolverConfig(SchedulingBaseModel):
    constraints: dict[str, ConstraintConfig]
    objectives: dict[str, ObjectiveConfig]


def create_base_solver_config() -> SolverConfig:
    """Create the deliberately configured baseline solver setup.

    This is the current stable solver behavior. It is explicit on purpose:
    every registered constraint/objective must appear here.
    """
    return SolverConfig(
        constraints={
            MinimumStaffing.id: ConstraintConfig(enabled=True),
        },
        objectives={
            TemporaryBalanceGeneratedAssignments.id: ObjectiveConfig(
                enabled=True,
                weight=1,
            ),
        },
    )
