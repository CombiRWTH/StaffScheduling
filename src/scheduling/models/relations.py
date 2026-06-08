from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, Field


class Membership(BaseModel):
    """Employee membership in a station-local or jump-pool staffing pool."""

    employee_id: int = Field(gt=0)
    station_id: int = Field(gt=0)

    membership_type: Literal["local", "jump_pool", "external", "unknown"] = "local"

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

    assignment_type: Literal["planned", "fixed", "external", "management"] = "planned"

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

    availability_type: Literal[
        "unavailable",
        "vacation",
        "training",
        "free_weekend",
        "available_only",
    ]

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
    rule_type: Literal[
        "medical_night_ban",
        "night_watch_only",
        "weekday_early_only",
        "fixed_weekday_free",
        "does_not_count_for_minimum_staffing",
        "no_night_before_protected_free_time",
        "max_consecutive_days",
        "min_rest_time",
        "other",
    ]

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

    preference_type: Literal[
        "day_off",
        "shift_off",
        "shift_on",
        "work_any",
        "avoid_shift",
        "prefer_shift",
    ]

    date: Date | None = None
    weekdays: tuple[int, ...] | None = None
    shift_ids: tuple[str, ...] | None = None

    weight: int = Field(default=1, ge=0)
    source: str | None = None
