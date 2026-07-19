import logging
from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends

from scheduling.api.dependencies import get_timeoffice_service
from scheduling.api.web.schemas import SuccessResponse, UpdateWeightsRequest, WeightsRequestData
from scheduling.domain import PlanningMonth, SolverObjectiveWeights
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)

weights_router = APIRouter()


@weights_router.get("/weights")
async def get_weights(
    planning_unit: int,
    from_date: date,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, int]:
    planning_month = PlanningMonth(year=from_date.year, month=from_date.month)

    dataset = timeoffice.fetch_dataset(
        planning_unit_ids=(planning_unit,),
        planning_month=planning_month,
    )

    objective_weights = _objective_weights_for_planning_unit(
        planning_unit_id=planning_unit,
        objective_weights=dataset.objective_weights,
    )

    return _objective_weights_to_frontend(objective_weights)


def _objective_weights_for_planning_unit(
    *,
    planning_unit_id: int,
    objective_weights: tuple[SolverObjectiveWeights, ...],
) -> SolverObjectiveWeights:
    for weights in objective_weights:
        if weights.planning_unit_id == planning_unit_id:
            return weights

    return SolverObjectiveWeights.default_for_planning_unit(planning_unit_id)


def _objective_weights_to_frontend(weights: SolverObjectiveWeights) -> dict[str, int]:
    return {
        "after_night": weights.recovery_after_night_shift,
        "consecutive_days": weights.consecutive_working_days,
        "consecutive_nights": weights.consecutive_night_shifts,
        "fairness": weights.fairness,
        "free_weekend": weights.free_weekend,
        "hidden": weights.hidden_employee,
        "overtime": weights.overtime_penalty,
        "rotate": weights.shift_rotation,
        "second_weekend": weights.second_weekend_penalty,
        "wishes": weights.employee_wish,
    }


@weights_router.put("/weights")
async def put_weights(
    planning_unit: int,
    from_date: date,  # Die weights sind nicht monatsspezifisch -> Mit Frontend API abklären ob das benötigt wird
    request: UpdateWeightsRequest,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> SuccessResponse:
    objective_weights = _weights_request_to_domain(
        planning_unit_id=planning_unit,
        data=request.data,
    )

    timeoffice.replace_objective_weights(
        planning_unit_id=planning_unit,
        objective_weights=objective_weights,
    )

    return SuccessResponse()


def _weights_request_to_domain(
    *,
    planning_unit_id: int,
    data: WeightsRequestData,
) -> SolverObjectiveWeights:
    return SolverObjectiveWeights(
        planning_unit_id=planning_unit_id,
        recovery_after_night_shift=data.after_night,
        consecutive_working_days=data.consecutive_days,
        consecutive_night_shifts=data.consecutive_nights,
        fairness=data.fairness,
        free_weekend=data.free_weekend,
        hidden_employee=data.hidden,
        overtime_penalty=data.overtime,
        shift_rotation=data.rotate,
        second_weekend_penalty=data.second_weekend,
        employee_wish=data.wishes,
    )
