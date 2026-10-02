"""Publishing a reviewed schedule to the stations' planning targets, and clearing it again."""

from datetime import datetime
from enum import StrEnum

from app.domain.core import NonNegativeInt, PositiveId, SchedulingBaseModel
from app.domain.planning_month import PlanningMonth


class PublicationRequest(SchedulingBaseModel):
    """Publish the schedule under review that was received at `received_at` to exactly these stations' month."""

    planning_month: PlanningMonth
    planning_unit_ids: tuple[PositiveId, ...]
    received_at: datetime


class PublicationResult(SchedulingBaseModel):
    """What a committed publication or clear changed in the named stations' month."""

    planning_month: PlanningMonth
    planning_unit_ids: tuple[PositiveId, ...]
    removed_duties: NonNegativeInt
    """Previously published duties the operation replaced or cleared."""
    published_duties: NonNegativeInt
    """Duties written and read back; zero for a clear."""


class PublicationProblem(StrEnum):
    """Why a schedule was not published.

    CHANGED: the schedule under review is not the one the request names.
    NOT_ACCEPTED: the independent check did not accept the schedule.
    CONFLICT: an employee already has an absence or another duty on a duty's date.
    READ_BACK: the written duties read back differently, so the publication was rolled back.
    """

    CHANGED = "changed"
    NOT_ACCEPTED = "not_accepted"
    CONFLICT = "conflict"
    READ_BACK = "read_back"


class PublicationRejected(Exception):
    """A publication refused or rolled back for a stated reason; nothing was written."""

    def __init__(self, problem: PublicationProblem, message: str) -> None:
        super().__init__(message)
        self.problem = problem
