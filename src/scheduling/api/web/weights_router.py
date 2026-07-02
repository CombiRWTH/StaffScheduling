import logging
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.domain import PlanningMonth  # Hier muss später noch Wish stehen
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)

weights_router = APIRouter()


DEFAULT_WEIGHTS: dict[
    str, Any
] = {}  # TODO: Default weights sollten in der Datenbank stehen und später ausgelesen werden


@weights_router.get("/weights")
async def get_weights(
    planning_unit: int,
    from_date: date,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, Any]:
    """Return weights for a planning unit and month.

    TODO: Ersetzen des Kommentars fürs fetchen mit der richtigen Funktion
    TODO: Default weights in die Datenbank schreiben und die dann fetchen
    """
    # Wäre schöner, wenn Monat und Jahr im frontend übergeben werden -> ggf. noch ändern
    month = PlanningMonth(year=from_date.year, month=from_date.month)
    # weights = timeoffice.fetch_dataset(planning_unit_ids=(planning_unit,), planning_month=month).weights
    logger.info(
        "Fetching weights: planning_unit=%s planning_month=%s",
        planning_unit,
        month.label,
    )
    # if weights is None:
    #     TODO: weights = Methode fetch default weights oder so
    # TODO: Umwandeln der weights in die entsprechende json
    # return weights

    return DEFAULT_WEIGHTS  # Muss durch weights ersetzt werden und dann können Default weights gelöscht werden


@weights_router.put("/weights")
async def put_weights(
    planning_unit: int,
    from_date: date,
    request: dict[str, Any],  # Vielleicht schöner dem Request ein Schema zu geben
) -> dict[str, bool]:
    """Update weights for a planning unit and month.

    TODO: Überführen der Gewichte ins Domain + Schreiben der Gewichte in die Datenbank
    """
    month = PlanningMonth(year=from_date.year, month=from_date.month)
    weights_json = request.get("data", {})

    logger.info(
        "Received weights update: planning_unit=%s planning_month=%s weights=%s",
        planning_unit,
        month.label,
        weights_json,
    )
    # TODO: Überführen der weights_json in das Domain
    logger.info("Update Weights in Database")
    return {"success": True}
