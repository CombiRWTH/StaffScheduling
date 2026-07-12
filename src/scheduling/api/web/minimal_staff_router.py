import logging
from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.api.web.schemas import SuccessResponse, UpdateMinimalStaffRequest
from scheduling.domain import DemandRequirement, PlanningMonth, StaffLevel
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)


minimal_staff_router = APIRouter()

DAYS_OF_WEEK = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")

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

WEEKDAY_TO_ID = {
    "Mo": 1,
    "Di": 2,
    "Mi": 3,
    "Do": 4,
    "Fr": 5,
    "Sa": 6,
    "So": 7,
}


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


@minimal_staff_router.put("/minimal-staff")
async def put_minimal_staff(
    planning_unit: int,
    from_date: date,
    request: UpdateMinimalStaffRequest,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> SuccessResponse:
    planning_month = PlanningMonth(year=from_date.year, month=from_date.month)

    demand_requirements = _minimal_staff_request_to_domain(
        planning_unit=planning_unit,
        planning_month=planning_month,
        minimal_staff=request.data,
    )

    timeoffice.replace_minimal_staffing(
        planning_unit_id=planning_unit,
        demand_requirements=demand_requirements,
    )

    return SuccessResponse()


def _minimal_staff_request_to_domain(
    *,
    planning_unit: int,
    planning_month: PlanningMonth,
    minimal_staff: dict[str, dict[str, dict[str, int]]],
) -> tuple[DemandRequirement, ...]:
    requirements: list[DemandRequirement] = []

    for frontend_staff_level, demand_by_day in minimal_staff.items():
        staff_level = DOMAIN_STAFF_LEVEL_BY_FRONTEND[frontend_staff_level]

        for frontend_day, demand_by_shift in demand_by_day.items():
            weekday_iso = WEEKDAY_TO_ID[frontend_day]

            for shift_code, minimum_count in demand_by_shift.items():
                if minimum_count < 0:
                    raise ValueError("Minimal staff count must be >=0")

                if minimum_count == 0:
                    continue

                shift_id = _shift_id_from_shift_code(shift_code)

                for requirement_date in _dates_for_weekday(
                    planning_month=planning_month,
                    weekday_iso=weekday_iso,
                ):
                    requirements.append(
                        DemandRequirement(
                            planning_unit_id=planning_unit,
                            date=requirement_date,
                            shift_id=shift_id,
                            staff_level=staff_level,
                            required_count=minimum_count,
                        )
                    )

    return tuple(requirements)


def _shift_id_from_shift_code(shift_code: str) -> int:
    if shift_code not in FRONTEND_SHIFT_CODES:
        raise ValueError(f"Shift Code is not defined in frontend: shift_code={shift_code}.")

    for shift_id, shift_fact in TIMEOFFICE_FACTS.reference_shift_facts_by_id.items():
        if shift_fact.expected_code == shift_code:
            return shift_id

    raise ValueError(f"Unknown shift_code={shift_code}.")


def _dates_for_weekday(
    *,
    planning_month: PlanningMonth,
    weekday_iso: int,
) -> tuple[date, ...]:
    dates: list[date] = []

    current_date = planning_month.start
    while current_date <= planning_month.end:
        if current_date.isoweekday() == weekday_iso:
            dates.append(current_date)

        current_date += timedelta(days=1)

    return tuple(dates)
