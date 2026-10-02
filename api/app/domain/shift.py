from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator

from app.domain.core import NonEmptyStr, PositiveId, SchedulingBaseModel

ShiftId = PositiveId

MINUTES_PER_DAY = 24 * 60


class ShiftType(StrEnum):
    """Reduced shift type used by scheduling rules.

    This is not a full TimeOffice shift taxonomy. It only contains categories
    relevant for demand, night rules and the shift-order objective.
    """

    EARLY = "early"
    LATE = "late"
    NIGHT = "night"
    INTERMEDIATE = "intermediate"
    MANAGEMENT = "management"
    OTHER = "other"


class WorkSegment(SchedulingBaseModel):
    """One stretch of active work, in local minutes after midnight of the duty's start date."""

    start_minute: int = Field(ge=0, lt=2 * MINUTES_PER_DAY)
    end_minute: int = Field(gt=0, le=2 * MINUTES_PER_DAY)

    @model_validator(mode="after")
    def validate_segment(self) -> Self:
        if self.start_minute >= self.end_minute:
            raise ValueError("A work segment must end after it starts.")
        return self


class Shift(SchedulingBaseModel):
    """Scheduling-relevant view of a TimeOffice shift.

    `segments` are the evidenced active-work stretches; the gaps between them are unpaid breaks.
    `net_work_minutes` is the paid time booked on the monthly account, which can differ from the
    elapsed work time on a daylight-saving night. A shift lasts less than 24 hours and may end
    on the next date; the TimeOffice adapter maps raw shift IDs and segments into this model.
    """

    shift_id: ShiftId
    code: NonEmptyStr
    type: ShiftType
    segments: tuple[WorkSegment, ...] = Field(min_length=1)
    net_work_minutes: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_shift(self) -> Self:
        if any(a.end_minute > b.start_minute for a, b in zip(self.segments, self.segments[1:], strict=False)):
            raise ValueError("Shift segments must be ordered and must not overlap.")
        if self.start_minute >= MINUTES_PER_DAY:
            raise ValueError("A shift must start on its start date.")
        if self.end_minute - self.start_minute >= MINUTES_PER_DAY:
            raise ValueError("A shift must last less than 24 hours.")
        return self

    @property
    def start_minute(self) -> int:
        return self.segments[0].start_minute

    @property
    def end_minute(self) -> int:
        """Local minutes after midnight of the start date; beyond 1440 the shift ends on the next date."""
        return self.segments[-1].end_minute


class ShiftOption(SchedulingBaseModel):
    """A canonical shift as offered for selection in configuration; timing stays with `Shift`."""

    shift_id: ShiftId
    code: NonEmptyStr
    type: ShiftType
