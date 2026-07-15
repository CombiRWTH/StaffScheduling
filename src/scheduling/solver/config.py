from typing import Any

from pydantic import Field

from scheduling.domain import SchedulingBaseModel
from scheduling.solver.cp_sat.constraints.availabilities_constraint import AvailabilitiesConstraint
from scheduling.solver.cp_sat.constraints.free_day_after_night_shift_phase import FreeDayAfterNightShiftPhase
from scheduling.solver.cp_sat.constraints.hierarchy_of_intermediate_shifts import HierarchyOfIntermediateShifts
from scheduling.solver.cp_sat.constraints.minimum_staffing import MinimumStaffing
from scheduling.solver.cp_sat.constraints.one_assignment_per_day import OneAssignmentPerDay
from scheduling.solver.cp_sat.constraints.rounds_in_early_shift import RoundsInEarlyShift
from scheduling.solver.cp_sat.constraints.target_working_time import TargetWorkingTime
from scheduling.solver.cp_sat.objectives.every_second_weekend_free import EverySecondWeekendFree
from scheduling.solver.cp_sat.objectives.fair_preferences import FairPreferencesObjective
from scheduling.solver.cp_sat.objectives.free_day_after_night_shift_phase import FreeDaysAfterNightShiftPhase
from scheduling.solver.cp_sat.objectives.free_days_near_weekend import FreeDaysNearWeekend
from scheduling.solver.cp_sat.objectives.minimize_consecutive_night_shifts import MinimizeConsecutiveNightShifts
from scheduling.solver.cp_sat.objectives.minimize_overtime import MinimizeOvertime
from scheduling.solver.cp_sat.objectives.not_too_many_consecutive_days import NotTooManyConsecutiveDays
from scheduling.solver.cp_sat.objectives.prefer_own_planning_unit import PreferOwnPlanningUnit
from scheduling.solver.cp_sat.objectives.preferred_block_length import PreferredBlockLength
from scheduling.solver.cp_sat.objectives.rotate_shits_foward import RotateShiftsForward
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
            FreeDayAfterNightShiftPhase.id: ConstraintConfig(enabled=True),
            RoundsInEarlyShift.id: ConstraintConfig(enabled=True),
            AvailabilitiesConstraint.id: ConstraintConfig(enabled=True),
            HierarchyOfIntermediateShifts.id: ConstraintConfig(enabled=True),
            OneAssignmentPerDay.id: ConstraintConfig(enabled=True),
            TargetWorkingTime.id: ConstraintConfig(enabled=True),
        },
        objectives={
            TemporaryBalanceGeneratedAssignments.id: ObjectiveConfig(
                enabled=True,
                weight=1,
            ),
            MinimizeOvertime.id: ObjectiveConfig(
                enabled=True,
                weight=100,
            ),
            NotTooManyConsecutiveDays.id: ObjectiveConfig(
                enabled=True,
                weight=1,
            ),
            PreferredBlockLength.id: ObjectiveConfig(
                enabled=True,
                weight=1,
            ),
            RotateShiftsForward.id: ObjectiveConfig(
                enabled=True,
                weight=1,
            ),
            PreferOwnPlanningUnit.id: ObjectiveConfig(
                enabled=True,
                weight=1,
            ),
            EverySecondWeekendFree.id: ObjectiveConfig(enabled=True, weight=1),
            FairPreferencesObjective.id: ObjectiveConfig(
                enabled=True,
                weight=1,
            ),
            FreeDaysAfterNightShiftPhase.id: ObjectiveConfig(enabled=True, weight=1),
            FreeDaysNearWeekend.id: ObjectiveConfig(enabled=True, weight=1),
            MinimizeConsecutiveNightShifts.id: ObjectiveConfig(enabled=True, weight=1),
        },
    )
