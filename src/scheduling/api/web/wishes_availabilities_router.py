import json
import logging
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.api.web.schemas import CreateWishesAndBlockedRequest, SuccessResponse, WishesAndBlockedEmployeeRequest
from scheduling.domain import Availability, AvailabilityType, Employee, PlanningMonth, Wish, WishType
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)

wishes_and_availabilities_router = APIRouter()


@wishes_and_availabilities_router.get("/wishes-and-blocked")
async def get_wishes_and_blocked(
    planning_unit: int,
    from_date: date,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, list[dict[str, Any]]]:
    from_date_year, from_date_month = from_date.year, from_date.month
    month = PlanningMonth(year=from_date_year, month=from_date_month)

    dataset = timeoffice.fetch_dataset(
        planning_unit_ids=(planning_unit,),
        planning_month=month,
    )

    employee_wishes_blocked = [
        _wishes_and_availability_to_frontend(
            employee=employee,
            wishes=dataset.wishes,
            availability=dataset.availability,
        )
        for employee in dataset.employees
    ]
    logger.warning(
        "DEBUG wishes/availability response: %s",
        json.dumps(
            {
                "employees": [
                    employee_wish_block
                    for employee_wish_block in employee_wishes_blocked
                    if _has_any_wishes_or_availability(employee_wish_block)
                ]
            }
        ),
    )

    return {
        "employees": [
            employee_wish_block
            for employee_wish_block in employee_wishes_blocked
            if _has_any_wishes_or_availability(employee_wish_block)
        ]
    }


def _has_any_wishes_or_availability(employee_block: dict[str, Any]) -> bool:
    return any(
        employee_block[field]
        for field in (
            "blocked_days",
            "blocked_shifts",
            "wish_days",
            "wish_shifts",
            "work_days",
            "work_shifts",
        )
    )


def _wishes_and_availability_to_frontend(
    *,
    employee: Employee,
    wishes: tuple[Wish, ...],
    availability: tuple[Availability, ...],
) -> dict[str, Any]:
    name, firstname = _split_display_name(employee.display_name)

    employee_wishes = [wish for wish in wishes if wish.employee_id == employee.employee_id]

    employee_availability = [item for item in availability if item.employee_id == employee.employee_id]

    return {
        "key": employee.employee_id,
        "firstname": firstname,
        "name": name,
        # Availability
        "blocked_days": [
            item.date.day for item in employee_availability if item.availability_type != AvailabilityType.AVAILABLE_ONLY
        ],
        "blocked_shifts": _blocked_shifts_to_frontend(employee_availability),
        "wish_days": [wish.date.day for wish in employee_wishes if wish.type == WishType.FREE_DAY],
        "wish_shifts": [
            [wish.date.day, _wish_shift_to_frontend(wish)]
            for wish in employee_wishes
            if wish.type == WishType.FREE_SHIFT
        ],
        "work_days": [wish.date.day for wish in employee_wishes if wish.type == WishType.PREFERRED_DAY],
        "work_shifts": [
            [wish.date.day, _wish_shift_to_frontend(wish)]
            for wish in employee_wishes
            if wish.type == WishType.PREFERRED_SHIFT
        ],
    }


def _blocked_shifts_to_frontend(
    availability_items: list[Availability],
) -> list[list[int | str]]:
    shift_ids_by_code = _reference_shift_ids_by_code()
    shift_codes_by_id = {shift_id: shift_code for shift_code, shift_id in shift_ids_by_code.items()}

    all_shift_codes = set(shift_ids_by_code)

    blocked_shifts: list[list[int | str]] = []

    for item in availability_items:
        if item.availability_type != AvailabilityType.AVAILABLE_ONLY:
            continue

        if item.shift_ids is None:
            continue

        allowed_shift_codes = {
            shift_codes_by_id[shift_id] for shift_id in item.shift_ids if shift_id in shift_codes_by_id
        }

        blocked_shift_codes = all_shift_codes - allowed_shift_codes

        for shift_code in sorted(blocked_shift_codes):
            blocked_shifts.append([item.date.day, shift_code])

    return blocked_shifts


def _reference_shift_ids_by_code() -> dict[str, int]:
    return {
        shift_fact.expected_code: shift_id
        for shift_id, shift_fact in TIMEOFFICE_FACTS.reference_shift_facts_by_id.items()
        if shift_fact.expected_code in {"F", "S", "N"}
    }


def _wish_shift_to_frontend(wish: Wish) -> str:
    if wish.shift_id is None:
        raise ValueError(f"{wish.type} wish requires shift_id.")

    shift_fact = TIMEOFFICE_FACTS.reference_shift_facts_by_id.get(wish.shift_id)

    if shift_fact is None:
        raise ValueError(f"Unknown reference shift for wish: employee_id={wish.employee_id} ")

    return shift_fact.expected_code


def _split_display_name(display_name: str) -> tuple[str, str]:
    name, _separator, firstname = display_name.partition(" ")
    return name, firstname


@wishes_and_availabilities_router.put("/wishes-and-blocked/{employee_id}")
async def replace_wishes_and_blocked(
    employee_id: int,
    planning_unit: int,
    from_date: date,
    request: CreateWishesAndBlockedRequest,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> SuccessResponse:
    if request.data.key != employee_id:
        raise ValueError("employee_id path parameter does not match request.data.key.")

    from_date_year, from_date_month = from_date.year, from_date.month
    planning_month = PlanningMonth(year=from_date_year, month=from_date_month)

    wishes = _wishes_employee_request_to_domain(
        employee=request.data,
        planning_unit=planning_unit,
        planning_month=planning_month,
    )
    print(wishes)
    """
    timeoffice.replace_wishes(
        planning_unit_id=planning_unit,
        planning_month=planning_month,
        employee_id=employee_id,
        wishes=wishes,
    )"""

    return SuccessResponse()


def _wishes_employee_request_to_domain(
    *,
    employee: WishesAndBlockedEmployeeRequest,
    planning_unit: int,
    planning_month: PlanningMonth,
) -> tuple[Wish, ...]:
    wishes: list[Wish] = []

    for day in employee.wish_days:
        wishes.append(
            Wish(
                employee_id=employee.key,
                planning_unit_id=planning_unit,
                date=date(planning_month.year, planning_month.month, day),
                type=WishType.PREFERRED_DAY,
            )
        )

    for day, shift_code in employee.wish_shifts:
        wishes.append(
            Wish(
                employee_id=employee.key,
                planning_unit_id=planning_unit,
                date=date(planning_month.year, planning_month.month, day),
                type=WishType.PREFERRED_SHIFT,
                shift_id=_shift_id_from_frontend(shift_code),
            )
        )

    for day in employee.blocked_days:
        wishes.append(
            Wish(
                employee_id=employee.key,
                planning_unit_id=planning_unit,
                date=date(planning_month.year, planning_month.month, day),
                type=WishType.FREE_DAY,
            )
        )

    for day, shift_code in employee.blocked_shifts:
        wishes.append(
            Wish(
                employee_id=employee.key,
                planning_unit_id=planning_unit,
                date=date(planning_month.year, planning_month.month, day),
                type=WishType.FREE_SHIFT,
                shift_id=_shift_id_from_frontend(shift_code),
            )
        )

    return tuple(wishes)


def _shift_id_from_frontend(shift_code: str) -> int:
    for shift_id, shift_fact in TIMEOFFICE_FACTS.reference_shift_facts_by_id.items():
        if shift_fact.expected_code == shift_code:
            return shift_id

    raise ValueError(f"Unknown shift code from wishes frontend: {shift_code!r}.")


@wishes_and_availabilities_router.delete("/wishes-and-blocked/{employee_id}")
async def delete_wishes_and_blocked(
    employee_id: int,
    planning_unit: int,
    from_date: date,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> SuccessResponse:
    from_date_year, from_date_month = from_date.year, from_date.month
    planning_month = PlanningMonth(year=from_date_year, month=from_date_month)

    timeoffice.delete_employee_wishes(
        planning_unit_id=planning_unit,
        planning_month=planning_month,
        employee_id=employee_id,
    )

    return SuccessResponse()
