from typing import Self

from pydantic import Field

from scheduling.domain.core import SchedulingBaseModel
from scheduling.domain.planning_unit import PlanningUnitId


class SolverObjectiveWeights(SchedulingBaseModel):
    """Weights for soft objectives used by the solver.

    These are planning-unit specific solver preferences.
    """

    planning_unit_id: PlanningUnitId

    recovery_after_night_shift: int = Field(default=3, ge=0)
    consecutive_working_days: int = Field(default=1, ge=0)
    consecutive_night_shifts: int = Field(default=2, ge=0)
    fairness: int = Field(default=3, ge=0)
    free_weekend: int = Field(default=3, ge=0)
    hidden_employee: int = Field(default=100, ge=0)
    overtime_penalty: int = Field(default=4, ge=0)
    shift_rotation: int = Field(default=1, ge=0)
    second_weekend_penalty: int = Field(default=1, ge=0)
    employee_wish: int = Field(default=3, ge=0)

    @classmethod
    def default_for_planning_unit(cls, planning_unit_id: PlanningUnitId) -> Self:
        return cls(planning_unit_id=planning_unit_id)
