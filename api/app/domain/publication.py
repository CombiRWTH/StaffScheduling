"""Publishing a reviewed schedule to the stations' planning targets, and clearing it again."""

from enum import StrEnum

from app.domain.core import NonNegativeInt, PositiveId, SchedulingBaseModel
from app.domain.planning_month import PlanningMonth


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
    """

    CHANGED = "changed"
    NOT_ACCEPTED = "not_accepted"
    CONFLICT = "conflict"


class PublicationRejected(Exception):
    """A publication refused for a reason the user can act on; nothing was written."""

    def __init__(self, problem: PublicationProblem, message: str) -> None:
        super().__init__(message)
        self.problem = problem
