from pydantic import BaseModel

from src.scheduling.models.core import PlanningPeriod
from src.scheduling.models.demand import Demand
from src.scheduling.models.employee import Employee
from src.scheduling.models.relations import (
    Assignment,
    Availability,
    Membership,
    Preference,
    Rule,
)
from src.scheduling.models.shift import Shift
from src.scheduling.models.station import Station


class StationMonthData(BaseModel):
    """Scheduling-relevant data for one station and one planning period.

    This is the canonical cache payload.
    It is not TimeOffice-specific and it is not solver-specific.
    """

    schema_version: int = 1

    station: Station
    period: PlanningPeriod

    source_plan_id: int | None = None

    employees: tuple[Employee, ...] = ()
    shifts: tuple[Shift, ...] = ()
    demand: tuple[Demand, ...] = ()
    memberships: tuple[Membership, ...] = ()
    assignments: tuple[Assignment, ...] = ()
    availability: tuple[Availability, ...] = ()
    rules: tuple[Rule, ...] = ()
    preferences: tuple[Preference, ...] = ()


class SchedulingDataset(BaseModel):
    """Combined scheduling data for one solver run."""

    period: PlanningPeriod

    stations: tuple[Station, ...]
    regular_station_ids: tuple[int, ...]
    jump_pool_station_ids: tuple[int, ...] = ()

    employees: tuple[Employee, ...] = ()
    shifts: tuple[Shift, ...] = ()
    demand: tuple[Demand, ...] = ()
    memberships: tuple[Membership, ...] = ()
    assignments: tuple[Assignment, ...] = ()
    availability: tuple[Availability, ...] = ()
    rules: tuple[Rule, ...] = ()
    preferences: tuple[Preference, ...] = ()
