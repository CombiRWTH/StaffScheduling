import logging
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.api.web.schemas import CreateWishesAndBlockedRequest, SuccessResponse, WishesAndBlockedDatabaseRequest
from scheduling.domain import Employee, PlanningMonth, WeeklyWish, WishType
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)

weeklyWishes_router = APIRouter()


@weeklyWishes_router.get("/global-wishes-and-blocked")
async def get_global_wishes_and_blocked(
    planning_unit: int,
    from_date: date,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, list[dict[str, Any]]]:
    from_date_year, from_date_month = from_date.year, from_date.month
    planning_month = PlanningMonth(year=from_date_year, month=from_date_month)

    dataset = timeoffice.fetch_dataset(
        planning_unit_ids=(planning_unit,),
        planning_month=planning_month,
    )

    return {
        "employees": [
            _weekly_wishes_to_frontend(
                employee=employee,
                weekly_wishes=dataset.weekly_wishes,
            )
            for employee in dataset.employees
        ]
    }


def _weekly_wishes_to_frontend(
    *,
    employee: Employee,
    weekly_wishes: tuple[WeeklyWish, ...],
) -> dict[str, Any]:
    name, firstname = _split_display_name(employee.display_name)

    employee_wishes = [wish for wish in weekly_wishes if wish.employee_id == employee.employee_id]

    return {
        "key": employee.employee_id,
        "firstname": firstname,
        "name": name,
        "wish_days": [wish.weekday for wish in employee_wishes if wish.type == WishType.PREFERRED_DAY],
        "wish_shifts": [
            [wish.weekday, _weekly_wish_shift_to_frontend(wish)]
            for wish in employee_wishes
            if wish.type == WishType.PREFERRED_SHIFT
        ],
        "blocked_days": [wish.weekday for wish in employee_wishes if wish.type == WishType.FREE_DAY],
        "blocked_shifts": [
            [wish.weekday, _weekly_wish_shift_to_frontend(wish)]
            for wish in employee_wishes
            if wish.type == WishType.FREE_SHIFT
        ],
    }


def _weekly_wish_shift_to_frontend(wish: WeeklyWish) -> str:
    if wish.shift_id is None:
        raise ValueError(f"{wish.type} weekly wish requires shift_id.")

    shift_fact = TIMEOFFICE_FACTS.reference_shift_facts_by_id.get(wish.shift_id)

    if shift_fact is None:
        raise ValueError(f"Unknown reference shift for weekly wish: employee_id={wish.employee_id}")

    return shift_fact.expected_code


@weeklyWishes_router.put("/global-wishes-and-blocked")
async def put_global_wishes_and_blocked(
    planning_unit: int,
    from_date: date,
    request: CreateWishesAndBlockedRequest,
) -> SuccessResponse:
    from_date_year, from_date_month = from_date.year, from_date.month
    planning_month = PlanningMonth(year=from_date_year, month=from_date_month)

    weekly_wishes = _weekly_wishes_request_to_domain(
        request=request.data,
        planning_unit=planning_unit,
        planning_month=planning_month,
    )

    logger.info(
        "Received global wishes update: planning_unit=%s planning_month=%s weekly_wishes=%s",
        planning_unit,
        planning_month.label,
        len(weekly_wishes),
    )

    # TODO: In Datenbank schreiben

    return SuccessResponse()


def _weekly_wishes_request_to_domain(
    *,
    request: WishesAndBlockedDatabaseRequest,
    planning_unit: int,
    planning_month: PlanningMonth,
) -> tuple[WeeklyWish, ...]:
    weekly_wishes: list[WeeklyWish] = []

    for employee in request.employees:
        for weekday in employee.wish_days:
            weekly_wishes.append(
                WeeklyWish(
                    employee_id=employee.key,
                    planning_unit_id=planning_unit,
                    planning_month=planning_month,
                    weekday=weekday,
                    type=WishType.PREFERRED_DAY,
                )
            )

        for weekday, shift_code in employee.wish_shifts:
            weekly_wishes.append(
                WeeklyWish(
                    employee_id=employee.key,
                    planning_unit_id=planning_unit,
                    planning_month=planning_month,
                    weekday=weekday,
                    type=WishType.PREFERRED_SHIFT,
                    shift_id=_shift_id_from_frontend(shift_code),
                )
            )

        for weekday in employee.blocked_days:
            weekly_wishes.append(
                WeeklyWish(
                    employee_id=employee.key,
                    planning_unit_id=planning_unit,
                    planning_month=planning_month,
                    weekday=weekday,
                    type=WishType.FREE_DAY,
                )
            )

        for weekday, shift_code in employee.blocked_shifts:
            weekly_wishes.append(
                WeeklyWish(
                    employee_id=employee.key,
                    planning_unit_id=planning_unit,
                    planning_month=planning_month,
                    weekday=weekday,
                    type=WishType.FREE_SHIFT,
                    shift_id=_shift_id_from_frontend(shift_code),
                )
            )

    return tuple(weekly_wishes)


def _split_display_name(display_name: str) -> tuple[str, str]:
    name, _separator, firstname = display_name.partition(" ")
    return name, firstname


def _shift_id_from_frontend(shift_code: str) -> int:
    for shift_id, shift_fact in TIMEOFFICE_FACTS.reference_shift_facts_by_id.items():
        if shift_fact.expected_code == shift_code:
            return shift_id

    raise ValueError(f"Unknown shift code from wishes frontend: {shift_code!r}.")
