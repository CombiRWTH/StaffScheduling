"""Publish the schedule under review to its stations' planning targets, or clear a station month."""

from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, Query

from app.api.review import get_review
from app.api.shared import Month, Year, get_planning_source, planning_errors
from app.domain import Assignment, PlanningMonth, PositiveId, PublicationRequest, PublicationResult

router = APIRouter()


class PublishableReview(Protocol):
    def publishable(self, request: PublicationRequest) -> tuple[Assignment, ...]: ...


class PublicationTarget(Protocol):
    def publish(
        self, *, planning_month: PlanningMonth, planning_unit_ids: tuple[int, ...], assignments: tuple[Assignment, ...]
    ) -> PublicationResult: ...

    def clear(self, *, planning_month: PlanningMonth, planning_unit_ids: tuple[int, ...]) -> PublicationResult: ...


Reviewer = Annotated[PublishableReview, Depends(get_review)]
Target = Annotated[PublicationTarget, Depends(get_planning_source)]
StationIds = Annotated[list[PositiveId], Query(min_length=1)]

INVALID = "Invalid publication: name configured stations with a target plan for the month."
INCOMPLETE = (
    "TimeOffice data for the publication is incomplete or ambiguous (target plans, memberships or shift catalog); "
    "nothing was changed."
)


@router.post(
    "/publication",
    responses={409: {"description": "Not published; `problem` names a reason the user can act on."}},
)
def publish(body: PublicationRequest, reviewer: Reviewer, target: Target) -> PublicationResult:
    """Replace the stations' published duties with the accepted schedule under review; success means committed.

    Only the review decides what may be published, so nothing else reaches the writer.
    """
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        return target.publish(
            planning_month=body.planning_month,
            planning_unit_ids=body.planning_unit_ids,
            assignments=reviewer.publishable(body),
        )


@router.delete("/publication")
def clear(planning_unit_ids: StationIds, year: Year, month: Month, target: Target) -> PublicationResult:
    """Remove the published duties of exactly these stations' month; absences, wishes and other plans stay."""
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        return target.clear(
            planning_month=PlanningMonth(year=year, month=month), planning_unit_ids=tuple(planning_unit_ids)
        )
