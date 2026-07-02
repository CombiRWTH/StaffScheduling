import logging
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.domain import Availability, AvailabilityType, Employee, PlanningMonth
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)

availability_router = APIRouter()


@availability_router.get("/availability")
async def get_availability(
    planning_unit: int,
    year: int,
    month: int,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, list[dict[str, Any]]]:
    month = PlanningMonth(year=year, month=month)

    dataset = timeoffice.fetch_dataset(
        planning_unit_ids=(planning_unit,),
        planning_month=month,
    )

    return {"employees": [_availability_to_frontend(employee, dataset.availability) for employee in dataset.employees]}


def _availability_to_frontend(
    employee: Employee,
    availabilities: tuple[Availability, ...],
) -> dict[str, Any]:
    name, firstname = _split_display_name(employee.display_name)

    employee_availabilities = [
        availability for availability in availabilities if availability.employee_id == employee.employee_id
    ]

    return {
        "key": employee.employee_id,
        "firstname": firstname,
        "name": name,
        "availability_days": [
            availability.date.day
            for availability in employee_availabilities
            if availability.availability_type == AvailabilityType.AVAILABLE_ONLY
        ],
        "unavailability_days": [
            availability.date.day
            for availability in employee_availabilities
            if availability.availability_type != AvailabilityType.AVAILABLE_ONLY
        ],
    }


def _split_display_name(display_name: str) -> tuple[str, str]:
    name, _separator, firstname = display_name.partition(" ")
    return name, firstname


@availability_router.put("/availability")
async def put_availability(
    planning_unit: int,
    from_date: date,
    request: dict[str, Any],  # Hier gerne wieder ein Request in Schema?
) -> dict[str, bool]:
    month = PlanningMonth(year=from_date.year, month=from_date.month)
    availability_json = request.get("data", {})

    logger.info(
        "Received availability update: planning_unit=%s planning_month=%s availability=%s",
        planning_unit,
        month.label,
        availability_json,
    )
    # TODO: Mappen der JSON auf das Domain
    # TODO: Aufruf der Datenbank

    logger.info("Update availability in database")

    return {"success": True}


# TODO: Global Availabilities fehlen und werden zur Zeit nicht mit modelliert
