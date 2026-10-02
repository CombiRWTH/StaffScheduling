"""An employee's monthly availability and wishes; every write names exactly one employee and date."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Path, status

from app.api.planning import Month, Source, Year, planning_errors
from app.domain import AvailabilityEntry, EmployeeCalendar, PlanningMonth, PositiveId, WishEntry

router = APIRouter()

EmployeePath = Annotated[PositiveId, Path()]

INVALID = "Invalid entry: use a planned employee, a valid date and reference shifts."
INCOMPLETE = "Availability data is incomplete. Verify memberships, absence codes and reference shifts."


@router.get("/availability")
def get_employee_calendar(employee_id: PositiveId, year: Year, month: Month, source: Source) -> EmployeeCalendar:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        return source.get_employee_calendar(
            employee_id=employee_id, planning_month=PlanningMonth(year=year, month=month)
        )


@router.put("/availability/{employee_id}/{day}")
def put_availability(
    employee_id: EmployeePath, day: date, entry: AvailabilityEntry, source: Source
) -> AvailabilityEntry:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        source.set_availability(employee_id=employee_id, day=day, entry=entry)
    return entry


@router.delete("/availability/{employee_id}/{day}", status_code=status.HTTP_204_NO_CONTENT)
def delete_availability(employee_id: EmployeePath, day: date, source: Source) -> None:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        source.set_availability(employee_id=employee_id, day=day, entry=None)


@router.put("/wishes/{employee_id}/{day}")
def put_wish(employee_id: EmployeePath, day: date, entry: WishEntry, source: Source) -> WishEntry:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        source.set_wish(employee_id=employee_id, day=day, entry=entry)
    return entry


@router.delete("/wishes/{employee_id}/{day}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wish(employee_id: EmployeePath, day: date, source: Source) -> None:
    with planning_errors(invalid=INVALID, incomplete=INCOMPLETE):
        source.set_wish(employee_id=employee_id, day=day, entry=None)
