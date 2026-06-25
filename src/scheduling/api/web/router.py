import logging
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.domain import Employee, PlanningMonth
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)


web_router = APIRouter()


@web_router.get("/employees")
async def get_employees(
    planning_unit: int,
    from_date: date,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, list[dict[str, Any]]]:
    month = PlanningMonth(year=from_date.year, month=from_date.month)
    employees = timeoffice.fetch_dataset(planning_unit_ids=(planning_unit,), planning_month=month).employees
    return {"employees": [_employee_to_frontend(employee) for employee in employees]}


def _employee_to_frontend(employee: Employee) -> dict[str, Any]:
    name, firstname = _split_display_name(employee.display_name)

    return {
        "key": employee.employee_id,
        "name": name,
        "firstname": firstname,
        "type": employee.staff_level.value,
    }


def _split_display_name(display_name: str) -> tuple[str, str]:
    name, _separator, firstname = display_name.partition(" ")
    return name, firstname
