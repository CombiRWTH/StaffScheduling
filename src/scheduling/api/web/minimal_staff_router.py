import logging
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.api.web.schemas import SuccessResponse
from scheduling.domain import DemandRequirement, PlanningMonth, StaffLevel
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)


minimal_staff_router = APIRouter()

DAYS_OF_WEEK = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")

WEEKDAY_NAME_BY_FRONTEND_DAY = {
    "Mo": "Montag",
    "Di": "Dienstag",
    "Mi": "Mittwoch",
    "Do": "Donnerstag",
    "Fr": "Freitag",
    "Sa": "Samstag",
    "So": "Sonntag",
}

FRONTEND_STAFF_LEVEL_BY_DOMAIN = {
    StaffLevel.TRAINEE: "Azubi",
    StaffLevel.PROFESSIONAL: "Fachkraft",
    StaffLevel.ASSISTANT: "Hilfskraft",
}

DOMAIN_STAFF_LEVEL_BY_FRONTEND = {
    "Azubi": StaffLevel.TRAINEE,
    "Fachkraft": StaffLevel.PROFESSIONAL,
    "Hilfskraft": StaffLevel.ASSISTANT,
}

FRONTEND_STAFF_LEVELS = ("Azubi", "Fachkraft", "Hilfskraft")

FRONTEND_SHIFT_CODES = ("F", "S", "N", "Z")


@minimal_staff_router.get("/minimal-staff")
async def get_minimal_staff(
    planning_unit: int,
    from_date: date,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, dict[str, dict[str, int]]]:
    month = PlanningMonth(year=from_date.year, month=from_date.month)

    dataset = timeoffice.fetch_dataset(
        planning_unit_ids=(planning_unit,),
        planning_month=month,
    )

    return _minimal_staff_to_frontend(dataset.demand_requirements)


def _minimal_staff_to_frontend(
    demand_requirements: tuple[DemandRequirement, ...],
) -> dict[str, dict[str, dict[str, int]]]:
    output = _empty_minimal_staff_response()

    for requirement in demand_requirements:
        staff_level = FRONTEND_STAFF_LEVEL_BY_DOMAIN[requirement.staff_level]
        day = DAYS_OF_WEEK[requirement.date.isoweekday() - 1]
        shift_code = _shift_code_from_shift_id(requirement.shift_id)

        output[staff_level][day][shift_code] = requirement.required_count

    return output


def _empty_minimal_staff_response() -> dict[str, dict[str, dict[str, int]]]:
    return {
        staff_level: {day: dict.fromkeys(FRONTEND_SHIFT_CODES, 0) for day in DAYS_OF_WEEK}
        for staff_level in FRONTEND_STAFF_LEVELS
    }


def _shift_code_from_shift_id(shift_id: int) -> str:
    shift_fact = TIMEOFFICE_FACTS.reference_shift_facts_by_id.get(shift_id)

    if shift_fact is None:
        raise ValueError(f"Unknown reference shift_id={shift_id}.")

    if shift_fact.expected_code not in FRONTEND_SHIFT_CODES:
        raise ValueError(f"Unsupported minimal staff shift code={shift_fact.expected_code!r} for shift_id={shift_id}.")

    return shift_fact.expected_code


# TODO: minimal_staff put missing, unsure where in DB to write to
@minimal_staff_router.put("/minimal-staff")
async def put_minimal_staff(
    planning_unit: int,
    from_date: date,
    request: dict[str, dict[str, int]],
) -> dict[str, bool]:
    month = PlanningMonth(year=from_date.year, month=from_date.month)
    request_json = request.get("data", {})

    logger.info(
        "Received minimal staff update: planning_unit=%s planning_month=%s minimal_staff=%s",
        planning_unit,
        month.label,
        request_json,
    )

    logger.info("Update availability in database")

    return SuccessResponse()
