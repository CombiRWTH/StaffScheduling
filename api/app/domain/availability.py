from datetime import date as Date
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from app.domain.core import SchedulingBaseModel
from app.domain.employee import EmployeeId
from app.domain.shift import ShiftId


class AvailabilityType(StrEnum):
    """Employee availability constraint."""

    UNAVAILABLE = "unavailable"
    VACATION = "vacation"
    TRAINING = "training"
    FREE_DAY = "free_day"
    AVAILABLE_ONLY = "available_only"


class Availability(SchedulingBaseModel):
    """Employee availability constraint for a date.

    Wishes/preferences must not be represented here. They should become a
    separate soft-preference model later.
    """

    employee_id: EmployeeId
    date: Date
    availability_type: AvailabilityType

    reason: str | None = None
    source: str | None = None

    # Only used for AVAILABLE_ONLY. For absences/blockers this stays None.
    shift_ids: tuple[ShiftId, ...] | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> Self:
        if self.availability_type == AvailabilityType.AVAILABLE_ONLY:
            if not self.shift_ids:
                raise ValueError("AVAILABLE_ONLY availability must define shift_ids.")

        elif self.shift_ids is not None:
            raise ValueError(f"{self.availability_type} availability must not define shift_ids.")

        return self
