import logging
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.api.web.schemas import CreateWishesAndBlockedRequest, SuccessResponse, WishesAndBlockedEmployeeRequest
from scheduling.domain import Employee, PlanningMonth, Wish, WishType
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)

wishes_router = APIRouter()


@wishes_router.get("/wishes-and-blocked")
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

    return {
        "employees": [
            _wishes_to_frontend(
                employee=employee,
                wishes=dataset.wishes,
            )
            for employee in dataset.employees
        ]
    }


def _wishes_to_frontend(
    *,
    employee: Employee,
    wishes: tuple[Wish, ...],
) -> dict[str, Any]:
    name, firstname = _split_display_name(employee.display_name)

    employee_wishes = [wish for wish in wishes if wish.employee_id == employee.employee_id]

    return {
        "key": employee.employee_id,
        "firstname": firstname,
        "name": name,
        "wish_days": [wish.date.day for wish in employee_wishes if wish.type == WishType.PREFERRED_DAY],
        "wish_shifts": [
            [wish.date.day, _wish_shift_to_frontend(wish)]
            for wish in employee_wishes
            if wish.type == WishType.PREFERRED_SHIFT
        ],
        "blocked_days": [wish.date.day for wish in employee_wishes if wish.type == WishType.FREE_DAY],
        "blocked_shifts": [
            [wish.date.day, _wish_shift_to_frontend(wish)]
            for wish in employee_wishes
            if wish.type == WishType.FREE_SHIFT
        ],
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


@wishes_router.put("/wishes-and-blocked/{employee_id}")
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

    timeoffice.replace_wishes(
        planning_unit_id=planning_unit,
        planning_month=planning_month,
        employee_id=employee_id,
        wishes=wishes,
    )

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


@wishes_router.delete("/wishes-and-blocked/{employee_id}")
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
