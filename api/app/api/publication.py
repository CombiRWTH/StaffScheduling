"""Publish the schedule under review to its stations' planning targets, or clear a station month."""

from typing import Annotated, Any, Protocol

from fastapi import APIRouter, Depends, Query, Request

from app.api.shared import Month, Year, get_planning_source, planning_errors
from app.domain import PlanningMonth, PositiveId, PublicationResult
from app.solver.review import PublicationRequest

router = APIRouter()


class SchedulePublisher(Protocol):
    def publish(self, request: PublicationRequest) -> PublicationResult: ...


class PublicationTarget(Protocol):
    def clear(self, *, planning_month: PlanningMonth, planning_unit_ids: tuple[int, ...]) -> PublicationResult: ...


def get_publisher(request: Request) -> Any:
    return request.app.state.review


Publisher = Annotated[SchedulePublisher, Depends(get_publisher)]
Target = Annotated[PublicationTarget, Depends(get_planning_source)]
StationIds = Annotated[list[PositiveId], Query(min_length=1)]

INVALID = "Invalid publication: name configured stations with a target plan for the month."
INCOMPLETE = "TimeOffice targets or memberships are incomplete or ambiguous; nothing was changed."


@router.post(
    "/publication",
    responses={409: {"description": "Not published; `problem` names a reason the user can act on."}},
)
def publish(body: PublicationRequest, publisher: Publisher) -> PublicationResult:
    """Replace the stations' published duties with the accepted schedule under review; success means committed."""
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        return publisher.publish(body)


@router.delete("/publication")
def clear(planning_unit_ids: StationIds, year: Year, month: Month, target: Target) -> PublicationResult:
    """Remove the published duties of exactly these stations' month; absences, wishes and other plans stay."""
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        return target.clear(
            planning_month=PlanningMonth(year=year, month=month), planning_unit_ids=tuple(planning_unit_ids)
        )
