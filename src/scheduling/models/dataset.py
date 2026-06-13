from pydantic import BaseModel

from src.scheduling.models.core import PlanningPeriod
from src.scheduling.models.demand import Demand
from src.scheduling.models.employee import Employee
from src.scheduling.models.relations import Assignment, Availability, Membership, Preference, Rule
from src.scheduling.models.shift import Shift
from src.scheduling.models.station import Station


class SchedulingDataset(BaseModel):
    """Combined scheduling data for one solver run.

    This is the main application-facing data model. It represents the scheduling
    problem for one period and a selected set of stations.
    """

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
