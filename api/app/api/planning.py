from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.domain import PlanningInspection, PlanningMonth, PlanningOptions, PositiveId

router = APIRouter()


class PlanningSource(Protocol):
    """What these routes need from a planning database; TimeOffice is the current implementation."""

    def get_planning_options(self, *, planning_month: PlanningMonth) -> PlanningOptions: ...

    def inspect_employees(
        self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth
    ) -> PlanningInspection: ...


def get_planning_source(request: Request) -> PlanningSource:
    return request.app.state.planning_source


@router.get("/planning/options")
def get_planning_options(
    year: Annotated[int, Query(ge=2000, le=2200)],
    month: Annotated[int, Query(ge=1, le=12)],
    source: Annotated[PlanningSource, Depends(get_planning_source)],
) -> PlanningOptions:
    try:
        return source.get_planning_options(planning_month=PlanningMonth(year=year, month=month))
    except ValueError as error:
        raise HTTPException(
            status_code=409, detail="Planning options are incomplete; verify prepared unit/target data."
        ) from error


@router.get("/employees")
def get_employees(
    planning_unit_ids: Annotated[list[PositiveId], Query(min_length=1)],
    year: Annotated[int, Query(ge=2000, le=2200)],
    month: Annotated[int, Query(ge=1, le=12)],
    source: Annotated[PlanningSource, Depends(get_planning_source)],
) -> PlanningInspection:
    try:
        return source.inspect_employees(
            planning_unit_ids=tuple(planning_unit_ids),
            planning_month=PlanningMonth(year=year, month=month),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail="Employee inspection is incomplete. Verify stations, memberships, accounts and monthly evidence.",
        ) from error
