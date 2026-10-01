from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies import get_timeoffice_service
from app.domain import PlanningMonth, PositiveId
from app.employees.models import PlanningInspection, PlanningOptions
from app.timeoffice.service import TimeOfficeService

employee_router = APIRouter()


@employee_router.get("/planning/options")
def get_planning_options(
    year: Annotated[int, Query(ge=2000, le=2200)],
    month: Annotated[int, Query(ge=1, le=12)],
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> PlanningOptions:
    try:
        return timeoffice.get_planning_options(planning_month=PlanningMonth(year=year, month=month))
    except ValueError as error:
        raise HTTPException(
            status_code=409, detail="Planning options are incomplete; verify prepared unit/target data."
        ) from error


@employee_router.get("/employees")
def get_employees(
    planning_unit_ids: Annotated[list[PositiveId], Query(min_length=1)],
    year: Annotated[int, Query(ge=2000, le=2200)],
    month: Annotated[int, Query(ge=1, le=12)],
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> PlanningInspection:
    try:
        return timeoffice.inspect_employees(
            planning_unit_ids=tuple(planning_unit_ids),
            planning_month=PlanningMonth(year=year, month=month),
        )
    except ValueError as error:
        raise HTTPException(
            status_code=409,
            detail="Employee inspection is incomplete. Verify stations, memberships, accounts and monthly evidence.",
        ) from error
