"""Dated minimum staffing of one station month, and the weekly pattern that previews it."""

from typing import Annotated, Protocol

from fastapi import APIRouter, Depends

from app.api.shared import Month, Year, get_planning_source, planning_errors
from app.domain import DemandConfiguration, DemandPattern, MonthlyDemand, PlanningMonth, PlanningUnitId

router = APIRouter()


class DemandSource(Protocol):
    def get_demand(self, *, planning_unit_id: int, planning_month: PlanningMonth) -> DemandConfiguration: ...

    def save_demand(self, demand: MonthlyDemand) -> None: ...

    def preview_demand(self, pattern: DemandPattern) -> MonthlyDemand: ...


Source = Annotated[DemandSource, Depends(get_planning_source)]

INVALID = "Invalid staffing: choose a station with a target plan for the month and reference shifts."
INCOMPLETE = "Staffing data is incomplete. Verify the station and reference shifts."


@router.get("/demand")
def get_demand(planning_unit_id: PlanningUnitId, year: Year, month: Month, source: Source) -> DemandConfiguration:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        return source.get_demand(
            planning_unit_id=planning_unit_id, planning_month=PlanningMonth(year=year, month=month)
        )


@router.put("/demand")
def put_demand(demand: MonthlyDemand, source: Source) -> MonthlyDemand:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        source.save_demand(demand)
    return demand


@router.post("/demand/pattern")
def preview_pattern(pattern: DemandPattern, source: Source) -> MonthlyDemand:
    """The month's dated demand for a weekly pattern under the NRW calendar; nothing is saved."""
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        return source.preview_demand(pattern)
