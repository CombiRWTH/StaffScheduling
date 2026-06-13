from datetime import date as Date
from enum import StrEnum

from pydantic import BaseModel, Field


class MembershipType(StrEnum):
    LOCAL = "local"
    JUMP_POOL = "jump_pool"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class AssignmentType(StrEnum):
    PLANNED = "planned"
    FIXED = "fixed"
    EXTERNAL = "external"
    MANAGEMENT = "management"


class AvailabilityType(StrEnum):
    UNAVAILABLE = "unavailable"
    VACATION = "vacation"
    TRAINING = "training"
    FREE_WEEKEND = "free_weekend"
    AVAILABLE_ONLY = "available_only"


class RuleType(StrEnum):
    MEDICAL_NIGHT_BAN = "medical_night_ban"
    NIGHT_WATCH_ONLY = "night_watch_only"
    WEEKDAY_EARLY_ONLY = "weekday_early_only"
    FIXED_WEEKDAY_FREE = "fixed_weekday_free"
    DOES_NOT_COUNT_FOR_MINIMUM_STAFFING = "does_not_count_for_minimum_staffing"
    NO_NIGHT_BEFORE_PROTECTED_FREE_TIME = "no_night_before_protected_free_time"
    MAX_CONSECUTIVE_DAYS = "max_consecutive_days"
    MIN_REST_TIME = "min_rest_time"
    OTHER = "other"


class PreferenceType(StrEnum):
    DAY_OFF = "day_off"
    SHIFT_OFF = "shift_off"
    SHIFT_ON = "shift_on"
    WORK_ANY = "work_any"
    AVOID_SHIFT = "avoid_shift"
    PREFER_SHIFT = "prefer_shift"


class Membership(BaseModel):
    """Employee membership in a station-local or jump-pool staffing pool."""

    employee_id: int = Field(gt=0)
    station_id: int = Field(gt=0)

    membership_type: MembershipType = MembershipType.LOCAL

    valid_from: Date | None = None
    valid_until: Date | None = None

    is_home_station: bool | None = None
    is_substitute: bool | None = None


class Assignment(BaseModel):
    """Known, planned, fixed, or externally blocking assignment."""

    employee_id: int = Field(gt=0)
    date: Date
    shift_id: str
    station_id: int | None = None

    assignment_type: AssignmentType = AssignmentType.PLANNED

    counts_as_work: bool = True
    counts_for_minimum_staffing: bool | None = None

    source: str | None = None
    source_assignment_id: str | None = None
    source_shift_id: int | None = None
    source_code: str | None = None


class Availability(BaseModel):
    """Employee availability or unavailability information."""

    employee_id: int = Field(gt=0)
    date: Date

    availability_type: AvailabilityType

    shift_ids: tuple[str, ...] | None = None
    is_hard: bool = True

    source: str | None = None
    source_code: str | None = None
    source_id: str | None = None


class Rule(BaseModel):
    """Generic scheduling rule or special-case restriction.

    Keep this typed by rule_type. If one rule type becomes complex, extract a
    dedicated model later.
    """

    rule_id: str
    rule_type: RuleType

    employee_id: int | None = None
    station_id: int | None = None

    date: Date | None = None
    weekdays: tuple[int, ...] | None = None
    shift_ids: tuple[str, ...] | None = None
    qualification_id: str | None = None

    is_hard: bool = True
    description: str | None = None


class Preference(BaseModel):
    """Soft employee wish or recurring preference."""

    employee_id: int = Field(gt=0)

    preference_type: PreferenceType

    date: Date | None = None
    weekdays: tuple[int, ...] | None = None
    shift_ids: tuple[str, ...] | None = None

    weight: int = Field(default=1, ge=0)
    source: str | None = None
