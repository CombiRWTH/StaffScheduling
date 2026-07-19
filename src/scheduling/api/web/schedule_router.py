import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import APIRouter

logger = logging.getLogger(__name__)

PROCESSED_SOLUTIONS_DIR = Path("processed_solutions")

schedule_router = APIRouter()

# TODO: change solve router to use the lagacy solution writer already present in timeoffice
# TODO: adapt the get_schedule acordingly,
# TODO: use _get_solution_legacy to fetch the data so, when the db works, we only need to relace that one function


@schedule_router.get("/schedules/{schedule_id}")
async def get_schedule(
    planning_unit: int,
    from_date: date,
    schedule_id: str,
) -> Any:
    """Return a schedule solution for a planning unit and month."""
    return _get_solution_legacy(schedule_id)


def _get_solution_legacy(schedule_id: str) -> Any:
    """Read a processed solution from the legacy JSON files, place holder until database read write."""
    solution_path = PROCESSED_SOLUTIONS_DIR / f"{schedule_id}_processed.json"

    if not solution_path.is_file():
        return {"solution": None}

    with solution_path.open(encoding="utf-8") as f:
        return json.load(f)
