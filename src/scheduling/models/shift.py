from enum import StrEnum

from pydantic import BaseModel, Field


class ShiftKind(StrEnum):
    """Canonical solver-facing shift category."""

    EARLY = "early"
    INTERMEDIATE = "intermediate"
    LATE = "late"
    NIGHT = "night"
    MANAGEMENT = "management"
    OTHER = "other"


class Shift(BaseModel):
    """Canonical assignable shift definition.

    One Shift represents one assignable shift variant. Similar shifts can be
    grouped through shift_group_id, e.g. several TimeOffice night shifts can all
    belong to group "night" while keeping their own shift_id/source metadata.
    """

    shift_id: str
    shift_group_id: str | None = None
    name: str

    source_shift_id: int | None = None
    source_code: str | None = None

    kind: ShiftKind

    start_minute: int = Field(ge=0, lt=24 * 60)
    end_minute: int = Field(ge=0, lt=24 * 60)
    ends_next_day: bool = False

    break_minutes: int = Field(default=0, ge=0)
    net_work_minutes: int = Field(ge=0)

    assignable: bool = True
    counts_as_work: bool = True
    counts_for_minimum_staffing: bool = True
    is_night: bool = False
