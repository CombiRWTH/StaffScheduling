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
    return _generate_minimal_staff_requirements(dataset)


def _generate_minimal_staff_requirements(dataset: Any) -> dict[str, dict[str, dict[str, int]]]:
    level_map = {"trainee": "Azubi", "professional": "Fachkraft", "assistant": "Hilfskraft"}

    shift_map = {"early": "F", "late": "S", "night": "N"}

    days_of_week = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    output = {de_level: {day: {"F": 0, "N": 0, "S": 0} for day in days_of_week} for de_level in level_map.values()}

    if isinstance(dataset, dict):
        demand_data = dataset.get("demand_requirements", [])
    else:
        demand_data = getattr(dataset, "demand_requirements", [])

    if demand_data:
        for req in demand_data:
            if isinstance(req, dict):
                staff_level = req.get("staff_level")
                shift_type = req.get("shift_type")
                day_of_week = req.get("day_of_week")
                min_required = req.get("min_required", 0)
            else:
                staff_level = getattr(req, "staff_level", None)
                shift_type = getattr(req, "shift_type", None)
                day_of_week = getattr(req, "day_of_week", None)
                min_required = getattr(req, "min_required", 0)

            lvl = level_map.get(str(staff_level))
            shift = shift_map.get(str(shift_type))
            day = str(day_of_week)

            if lvl and shift and day in days_of_week:
                output[lvl][day][shift] = min_required
    else:
        # Default data
        output = {
            "Azubi": {
                "Di": {"F": 1, "N": 0, "S": 1},
                "Do": {"F": 1, "N": 0, "S": 1},
                "Fr": {"F": 1, "N": 0, "S": 1},
                "Mi": {"F": 1, "N": 0, "S": 1},
                "Mo": {"F": 1, "N": 0, "S": 1},
                "Sa": {"F": 1, "N": 0, "S": 1},
                "So": {"F": 1, "N": 0, "S": 1},
            },
            "Fachkraft": {
                "Di": {"F": 3, "N": 2, "S": 2},
                "Do": {"F": 3, "N": 2, "S": 2},
                "Fr": {"F": 3, "N": 2, "S": 2},
                "Mi": {"F": 4, "N": 2, "S": 2},
                "Mo": {"F": 3, "N": 2, "S": 2},
                "Sa": {"F": 2, "N": 1, "S": 2},
                "So": {"F": 2, "N": 1, "S": 2},
            },
            "Hilfskraft": {
                "Di": {"F": 2, "N": 0, "S": 2},
                "Do": {"F": 2, "N": 0, "S": 2},
                "Fr": {"F": 2, "N": 0, "S": 2},
                "Mi": {"F": 2, "N": 0, "S": 2},
                "Mo": {"F": 2, "N": 0, "S": 2},
                "Sa": {"F": 2, "N": 1, "S": 2},
                "So": {"F": 2, "N": 1, "S": 2},
            },
        }

    return output
