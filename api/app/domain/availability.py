from datetime import date as Date
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from app.domain.calendar import CalendarDay
from app.domain.core import NonEmptyStr, SchedulingBaseModel
from app.domain.employee import EmployeeId
from app.domain.planning_month import PlanningMonth
from app.domain.shift import ShiftId, ShiftOption
from app.domain.wish import Wish


class AvailabilityType(StrEnum):
    """Employee availability on a date."""

    UNAVAILABLE = "unavailable"
    VACATION = "vacation"
    TRAINING = "training"
    FREE_DAY = "free_day"
    AVAILABLE_ONLY = "available_only"


class AvailabilityEntry(SchedulingBaseModel):
    """What an employee's availability on one date is, without saying whose or when."""

    availability_type: AvailabilityType
    reason: NonEmptyStr | None = None

    # Only used for AVAILABLE_ONLY. For absences/blockers this stays None.
    shift_ids: tuple[ShiftId, ...] | None = None

    @model_validator(mode="after")
    def validate_availability(self) -> Self:
        if self.availability_type == AvailabilityType.AVAILABLE_ONLY:
            if not self.shift_ids:
                raise ValueError("AVAILABLE_ONLY availability must define shift_ids.")
            if len(set(self.shift_ids)) != len(self.shift_ids):
                raise ValueError("Duplicate shift_ids in availability.")

        elif self.shift_ids is not None:
            raise ValueError(f"{self.availability_type} availability must not define shift_ids.")

        return self


class Availability(AvailabilityEntry):
    """A date on which an employee must not be planned, or only for the listed shifts.

    Availability always binds planning; soft preferences are a `Wish`.
    """

    employee_id: EmployeeId
    date: Date
    source: str | None = None


class EmployeeCalendar(SchedulingBaseModel):
    """An employee's month: read-only native absences plus editable project availability and wishes."""

    employee_id: EmployeeId
    planning_month: PlanningMonth
    # Approved absences from the roster system; shown, never edited here.
    absences: tuple[Availability, ...]
    availability: tuple[Availability, ...]
    wishes: tuple[Wish, ...]
    calendar: tuple[CalendarDay, ...]
    shifts: tuple[ShiftOption, ...]
