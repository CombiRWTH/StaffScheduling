"""The schedule under review: the latest generated or imported bundle, kept in memory until the API restarts."""

from datetime import UTC, datetime
from enum import StrEnum

from app.domain import (
    Assignment,
    CalendarDay,
    CheckStatus,
    PlanningMonth,
    PlanningUnit,
    PlanningUnitType,
    PublicationProblem,
    PublicationRejected,
    PublicationRequest,
    SchedulingBaseModel,
    SchedulingDataset,
    Shift,
)
from app.domain.schedule import ScheduleTables
from app.solver.bundle import FileName, ScheduleBundle, ScheduleInput, to_json
from app.solver.models import Solution


class ReviewSource(StrEnum):
    GENERATION = "generation"
    IMPORT = "import"


class ScheduleReview(SchedulingBaseModel):
    """What the review page shows: the bundle's scope, solution and check, and its readable tables."""

    source: ReviewSource
    received_at: datetime
    planning_month: PlanningMonth
    planning_units: tuple[PlanningUnit, ...]
    shifts: tuple[Shift, ...]
    calendar: tuple[CalendarDay, ...]
    solution: Solution
    tables: ScheduleTables

    @property
    def station_ids(self) -> tuple[int, ...]:
        return tuple(unit.planning_unit_id for unit in self.planning_units if unit.type == PlanningUnitType.STATION)


class Review:
    """Hold one schedule for review and its downloadable files, and say whether a publication may take it.

    A generation that finds a schedule and a valid import each replace it; a run without a schedule
    and a rejected import leave it unchanged. Nothing is persisted, published or saved to a library.
    """

    def __init__(self) -> None:
        self._current: tuple[ScheduleBundle, ScheduleReview] | None = None

    def generated(self, dataset: SchedulingDataset, solution: Solution) -> None:
        """Review a generation's solution, if it found a schedule."""
        if solution.found:
            schedule_input = ScheduleInput.of(dataset)
            bundle = ScheduleBundle.solved(schedule_input, to_json(schedule_input), solution)
            self._show(bundle, ReviewSource.GENERATION)

    def imported(self, input_json: bytes, result_json: bytes) -> ScheduleReview:
        """Review an uploaded pair; raises InvalidBundle and keeps the current review if it is not a bundle."""
        return self._show(ScheduleBundle.read(input_json, result_json), ReviewSource.IMPORT)

    def current(self) -> ScheduleReview | None:
        return self._current[1] if self._current else None

    def file(self, name: FileName) -> bytes | None:
        """One file of the schedule under review, or None without one."""
        return self._current[0].files[name] if self._current else None

    def publishable(self, request: PublicationRequest) -> tuple[Assignment, ...]:
        """The assignments of the schedule under review if the request names it and its check accepted it.

        Raises PublicationRejected (`changed`, `not_accepted`) otherwise; nothing is written here.
        """
        current = self._current
        if current is None:
            raise PublicationRejected(PublicationProblem.CHANGED, "There is no schedule under review.")
        bundle, review = current
        if (
            review.received_at != request.received_at
            or review.planning_month != request.planning_month
            or set(review.station_ids) != set(request.planning_unit_ids)
        ):
            raise PublicationRejected(PublicationProblem.CHANGED, "The schedule under review is another one.")
        if bundle.check.status != CheckStatus.ACCEPTED:
            raise PublicationRejected(PublicationProblem.NOT_ACCEPTED, "Only an accepted schedule is published.")
        return bundle.result.solution.assignments

    def _show(self, bundle: ScheduleBundle, source: ReviewSource) -> ScheduleReview:
        dataset = bundle.input.dataset
        review = ScheduleReview(
            source=source,
            received_at=datetime.now(UTC),
            planning_month=dataset.planning_month,
            planning_units=dataset.planning_units,
            shifts=dataset.shifts,
            calendar=bundle.input.calendar,
            solution=bundle.result.solution,
            tables=bundle.tables,
        )
        self._current = (bundle, review)
        return review
