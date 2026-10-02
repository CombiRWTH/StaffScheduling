from collections.abc import Generator
from contextlib import contextmanager
from datetime import date
from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.domain import (
    Availability,
    DemandConfiguration,
    EmployeeCalendar,
    InvalidSelection,
    MonthlyDemand,
    PlanningInspection,
    PlanningMonth,
    PlanningOptions,
    PositiveId,
    Wish,
)

router = APIRouter()


class PlanningSource(Protocol):
    """What the routes need from a planning database; TimeOffice is the current implementation."""

    def get_planning_options(self, *, planning_month: PlanningMonth) -> PlanningOptions: ...

    def inspect_employees(
        self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth
    ) -> PlanningInspection: ...

    def get_employee_calendar(self, *, employee_id: int, planning_month: PlanningMonth) -> EmployeeCalendar: ...

    def save_availability(self, availability: Availability) -> None: ...

    def delete_availability(self, *, employee_id: int, day: date) -> None: ...

    def save_wish(self, wish: Wish) -> None: ...

    def delete_wish(self, *, employee_id: int, day: date) -> None: ...

    def get_demand(self, *, planning_unit_id: int, planning_month: PlanningMonth) -> DemandConfiguration: ...

    def save_demand(self, demand: MonthlyDemand) -> None: ...


def get_planning_source(request: Request) -> PlanningSource:
    return request.app.state.planning_source


Source = Annotated[PlanningSource, Depends(get_planning_source)]
Year = Annotated[int, Query(ge=2000, le=2200)]
Month = Annotated[int, Query(ge=1, le=12)]


@contextmanager
def planning_errors(*, incomplete: str, invalid: str = "Invalid request.") -> Generator[None]:
    """Invalid requests become 422 and incomplete source data 409, each with a useful message."""
    try:
        yield
    except InvalidSelection as error:
        raise HTTPException(status_code=422, detail=invalid) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=incomplete) from error


@router.get("/planning/options")
def get_planning_options(year: Year, month: Month, source: Source) -> PlanningOptions:
    with planning_errors(incomplete="Planning options are incomplete; verify prepared unit/target data."):
        return source.get_planning_options(planning_month=PlanningMonth(year=year, month=month))


@router.get("/employees")
def get_employees(
    planning_unit_ids: Annotated[list[PositiveId], Query(min_length=1)], year: Year, month: Month, source: Source
) -> PlanningInspection:
    with planning_errors(
        invalid="Invalid selection: choose configured stations with a target plan for the month.",
        incomplete="Employee inspection is incomplete. Verify stations, memberships, accounts and monthly evidence.",
    ):
        return source.inspect_employees(
            planning_unit_ids=tuple(planning_unit_ids), planning_month=PlanningMonth(year=year, month=month)
        )
