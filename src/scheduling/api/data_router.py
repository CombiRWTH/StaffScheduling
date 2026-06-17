import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from src.scheduling.api.dependencies import get_timeoffice_service
from src.scheduling.api.types import ApiDate
from src.scheduling.models import PlanningPeriod
from src.scheduling.models.assignment import AssignmentType
from src.scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)

data_router = APIRouter()


@data_router.get("/fetch")
def fetch_timeoffice_dataset(
    station_ids: Annotated[list[int], Query(alias="station")],
    start: Annotated[ApiDate, Query()],
    end: Annotated[ApiDate, Query()],
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, int]:
    period = PlanningPeriod(start=start, end=end)

    dataset = timeoffice.fetch_dataset(
        planning_unit_ids=tuple(station_ids),
        period=period,
    )

    return {
        "planning_units": len(dataset.planning_units),
        "plans": len(dataset.plans),
        "employees": len(dataset.employees),
        "plan_participants": len(dataset.plan_participants),
        "planning_unit_memberships": len(dataset.planning_unit_memberships),
        "shifts": len(dataset.shifts),
        "assignments": len(dataset.assignments),
        "planned_assignments": sum(
            assignment.assignment_type == AssignmentType.PLANNED for assignment in dataset.assignments
        ),
        "external_assignments": sum(
            assignment.assignment_type == AssignmentType.EXTERNAL for assignment in dataset.assignments
        ),
        "availability": len(dataset.availability),
        "demand_requirements": len(dataset.demand_requirements),
        "sunday_work_history": len(dataset.sunday_work_history),
    }
