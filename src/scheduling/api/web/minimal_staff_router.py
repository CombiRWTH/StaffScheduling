import logging
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.domain import PlanningMonth
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)


minimal_staff_router = APIRouter()


@minimal_staff_router.get("/minimal-staff")
async def get_minimal_staff_func(
    planning_unit: int, from_date: date, timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)]
) -> Any:
    """Return minimal staff requirements for a planning unit and month."""

    month = PlanningMonth(year=from_date.year, month=from_date.month)
    dataset = timeoffice.fetch_dataset(planning_unit_ids=(planning_unit,), planning_month=month)
    # return(_minimal_staff_to_frontend(dataset))
    return dataset
