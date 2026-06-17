from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from scheduling.models.core import (
    MinuteOfDay,
    NonEmptyStr,
    PositiveId,
    SchedulingBaseModel,
)

ShiftId = PositiveId


class ShiftKind(StrEnum):
    """Reduced shift kind used by scheduling rules.

    This is not a full TimeOffice shift taxonomy. It only contains categories
    relevant for demand, rest rules, night rules, and project-specific work.
    """

    EARLY = "early"
    LATE = "late"
    NIGHT = "night"
    INTERMEDIATE = "intermediate"
    MANAGEMENT = "management"
    OTHER = "other"


class StaffingDemandRole(StrEnum):
    """How a shift relates to staffing demand."""

    REQUIRED_MINIMUM = "required_minimum"
    OPTIONAL_COVERAGE = "optional_coverage"
    NON_MINIMUM_WORK = "non_minimum_work"


class Shift(SchedulingBaseModel):
    """Scheduling-relevant view of a TimeOffice shift.

    The TimeOffice adapter maps raw shift IDs/types/codes into this reduced
    model. The solver should use this model, not raw TimeOffice catalog fields.
    """

    shift_id: ShiftId
    code: NonEmptyStr

    kind: ShiftKind
    staffing_role: StaffingDemandRole

    start_minute: MinuteOfDay
    end_minute: MinuteOfDay

    # Net paid/planned work time used for monthly target-hour balancing.
    net_work_minutes: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_shift(self) -> Self:
        if self.start_minute == self.end_minute:
            raise ValueError("Shift start_minute and end_minute must differ.")

        return self
