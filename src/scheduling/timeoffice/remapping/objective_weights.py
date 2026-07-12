from scheduling.domain import SolverObjectiveWeights
from scheduling.domain.core import SchedulingBaseModel


class TimeOfficeObjectiveWeightWriteRow(SchedulingBaseModel):
    planning_unit_id: int
    objective_name: str
    weight: int


OBJECTIVE_NAMES = (
    "recovery_after_night_shift",
    "consecutive_working_days",
    "consecutive_night_shifts",
    "fairness",
    "free_weekend",
    "hidden_employee",
    "overtime_penalty",
    "shift_rotation",
    "second_weekend_penalty",
    "employee_wish",
)


def map_objective_weights_to_timeoffice_rows(
    objective_weights: SolverObjectiveWeights,
) -> tuple[TimeOfficeObjectiveWeightWriteRow, ...]:
    return tuple(
        TimeOfficeObjectiveWeightWriteRow(
            planning_unit_id=objective_weights.planning_unit_id,
            objective_name=objective_name,
            weight=getattr(objective_weights, objective_name),
        )
        for objective_name in OBJECTIVE_NAMES
    )
