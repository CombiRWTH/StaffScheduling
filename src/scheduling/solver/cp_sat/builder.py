from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from scheduling.domain import SchedulingDataset
from scheduling.solver.config import SolverConfig, create_base_solver_config
from scheduling.solver.cp_sat.constraint import Constraint
from scheduling.solver.cp_sat.constraints.minimum_staffing import MinimumStaffing
from scheduling.solver.cp_sat.context import SolverContext, create_context
from scheduling.solver.cp_sat.objective import Objective, WeightedPenalty, minimize_weighted_penalties
from scheduling.solver.cp_sat.objectives.temporary_balance_generated_assignments import (
    TemporaryBalanceGeneratedAssignments,
)
from scheduling.solver.cp_sat.objectives.every_second_weekend_free import EverySecondWeekendFree
from scheduling.solver.cp_sat.objectives.free_day_after_night_shift_phase import FreeDaysAfterNightShiftPhase
from scheduling.solver.cp_sat.objectives.free_days_near_weekend import FreeDaysNearWeekend
from scheduling.solver.cp_sat.objectives.minimize_consecutive_night_shifts import MinimizeConsecutiveNightShifts

from scheduling.solver.cp_sat.variables import create_assignment_variables

CP_SAT_CONSTRAINTS: tuple[Constraint, ...] = (MinimumStaffing(),)

CP_SAT_OBJECTIVES: tuple[Objective, ...] = (TemporaryBalanceGeneratedAssignments(),
                                            EverySecondWeekendFree(),
                                            FreeDaysAfterNightShiftPhase(),
                                            MinimizeConsecutiveNightShifts())


@dataclass(frozen=True, slots=True)
class ResolvedConstraint:
    constraint: Constraint
    enabled: bool
    params: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ResolvedObjective:
    objective: Objective
    enabled: bool
    weight: int
    params: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class CpSatBuildResult:
    ctx: SolverContext
    constraints: tuple[ResolvedConstraint, ...]
    objectives: tuple[ResolvedObjective, ...]
    weighted_penalty_count: int
    has_objective: bool

    @property
    def applied_constraint_ids(self) -> tuple[str, ...]:
        return tuple(resolved.constraint.id for resolved in self.constraints if resolved.enabled)

    @property
    def applied_objective_ids(self) -> tuple[str, ...]:
        return tuple(resolved.objective.id for resolved in self.objectives if resolved.enabled)


@dataclass(frozen=True, slots=True)
class CpSatModelBuilder:
    """Build CP-SAT models from configured stateless constraints and objectives."""

    constraints: tuple[Constraint, ...]
    objectives: tuple[Objective, ...]
    config: SolverConfig

    def build(self, dataset: SchedulingDataset) -> CpSatBuildResult:
        ctx = create_context(dataset=dataset)

        create_assignment_variables(ctx)

        resolved_constraints = resolve_constraints(
            constraints=self.constraints,
            config=self.config,
        )
        resolved_objectives = resolve_objectives(
            objectives=self.objectives,
            config=self.config,
        )

        weighted_penalties: list[WeightedPenalty] = []

        for resolved in resolved_constraints:
            if not resolved.enabled:
                continue

            diagnostics = resolved.constraint.add_to_model(ctx, params=resolved.params)
            ctx.diagnostics.extend(diagnostics)

        for resolved in resolved_objectives:
            if not resolved.enabled:
                continue

            penalties = resolved.objective.add_to_model(ctx, params=resolved.params)

            weighted_penalties.extend(
                WeightedPenalty(
                    penalty=penalty,
                    weight=resolved.weight,
                )
                for penalty in penalties
            )

        has_objective = minimize_weighted_penalties(
            model=ctx.model,
            penalties=tuple(weighted_penalties),
        )

        return CpSatBuildResult(
            ctx=ctx,
            constraints=resolved_constraints,
            objectives=resolved_objectives,
            weighted_penalty_count=len(weighted_penalties),
            has_objective=has_objective,
        )


def create_cp_sat_model_builder() -> CpSatModelBuilder:
    config = create_base_solver_config()

    return CpSatModelBuilder(
        constraints=CP_SAT_CONSTRAINTS,
        objectives=CP_SAT_OBJECTIVES,
        config=config,
    )


def resolve_constraints(
    *,
    constraints: tuple[Constraint, ...],
    config: SolverConfig,
) -> tuple[ResolvedConstraint, ...]:
    constraints_by_id = _constraints_by_id(constraints)

    _validate_config_keys(
        configured_ids=config.constraints.keys(),
        registered_ids=constraints_by_id.keys(),
        kind="constraint",
    )

    resolved: list[ResolvedConstraint] = []

    for constraint in constraints:
        raw_config = config.constraints[constraint.id]

        if not raw_config.enabled and constraint.required:
            raise ValueError(f"Required constraint cannot be disabled: {constraint.id}")

        resolved.append(
            ResolvedConstraint(
                constraint=constraint,
                enabled=raw_config.enabled,
                params=raw_config.params,
            )
        )

    return tuple(resolved)


def resolve_objectives(
    *,
    objectives: tuple[Objective, ...],
    config: SolverConfig,
) -> tuple[ResolvedObjective, ...]:
    objectives_by_id = _objectives_by_id(objectives)

    _validate_config_keys(
        configured_ids=config.objectives.keys(),
        registered_ids=objectives_by_id.keys(),
        kind="objective",
    )

    resolved: list[ResolvedObjective] = []

    for objective in objectives:
        raw_config = config.objectives[objective.id]

        if raw_config.enabled and raw_config.weight <= 0:
            raise ValueError(
                f"Enabled objective must have a positive weight: {objective.id} weight={raw_config.weight}"
            )

        resolved.append(
            ResolvedObjective(
                objective=objective,
                enabled=raw_config.enabled,
                weight=raw_config.weight,
                params=raw_config.params,
            )
        )

    return tuple(resolved)


def _constraints_by_id(constraints: tuple[Constraint, ...]) -> dict[str, Constraint]:
    by_id: dict[str, Constraint] = {}

    for constraint in constraints:
        if constraint.id in by_id:
            raise ValueError(f"Duplicate constraint id registered: {constraint.id}")

        by_id[constraint.id] = constraint

    return by_id


def _objectives_by_id(objectives: tuple[Objective, ...]) -> dict[str, Objective]:
    by_id: dict[str, Objective] = {}

    for objective in objectives:
        if objective.id in by_id:
            raise ValueError(f"Duplicate objective id registered: {objective.id}")

        by_id[objective.id] = objective

    return by_id


def _validate_config_keys(
    *,
    configured_ids: Iterable[str],
    registered_ids: Iterable[str],
    kind: str,
) -> None:
    configured = set(configured_ids)
    registered = set(registered_ids)

    unknown_ids = configured - registered
    missing_ids = registered - configured

    if unknown_ids:
        unknown = ", ".join(sorted(unknown_ids))
        raise ValueError(f"Unknown solver {kind} config id(s): {unknown}")

    if missing_ids:
        missing = ", ".join(sorted(missing_ids))
        raise ValueError(f"Missing solver {kind} config id(s): {missing}")
