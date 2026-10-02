"""An employee's monthly availability and wishes; every write names exactly one employee and date."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, Response, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.api.planning import Month, Source, Year, planning_errors
from app.domain import (
    Availability,
    AvailabilityType,
    EmployeeCalendar,
    NonEmptyStr,
    PlanningMonth,
    PositiveId,
    SchedulingBaseModel,
    ShiftId,
    Wish,
    WishType,
)

router = APIRouter()

EmployeePath = Annotated[PositiveId, Path()]

INVALID = "Invalid entry: use a planned employee, a valid date and reference shifts."
INCOMPLETE = "Availability data is incomplete. Verify memberships, absence codes and reference shifts."


class AvailabilityEntry(SchedulingBaseModel):
    availability_type: AvailabilityType
    shift_ids: tuple[ShiftId, ...] | None = None
    reason: NonEmptyStr | None = None


class WishEntry(SchedulingBaseModel):
    type: WishType
    shift_id: ShiftId | None = None


@router.get("/availability")
def get_employee_calendar(employee_id: PositiveId, year: Year, month: Month, source: Source) -> EmployeeCalendar:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        return source.get_employee_calendar(
            employee_id=employee_id, planning_month=PlanningMonth(year=year, month=month)
        )


@router.put("/availability/{employee_id}/{day}")
def put_availability(employee_id: EmployeePath, day: date, entry: AvailabilityEntry, source: Source) -> Availability:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        try:
            availability = Availability(employee_id=employee_id, date=day, **entry.model_dump())
        except ValidationError as error:
            raise RequestValidationError(error.errors()) from error
        source.save_availability(availability)
        return availability


@router.delete("/availability/{employee_id}/{day}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability(employee_id: EmployeePath, day: date, source: Source) -> Response:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        source.delete_availability(employee_id=employee_id, day=day)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/wishes/{employee_id}/{day}")
def put_wish(employee_id: EmployeePath, day: date, entry: WishEntry, source: Source) -> Wish:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        try:
            wish = Wish(employee_id=employee_id, date=day, **entry.model_dump())
        except ValidationError as error:
            raise RequestValidationError(error.errors()) from error
        source.save_wish(wish)
        return wish


@router.delete("/wishes/{employee_id}/{day}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wish(employee_id: EmployeePath, day: date, source: Source) -> Response:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        source.delete_wish(employee_id=employee_id, day=day)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
