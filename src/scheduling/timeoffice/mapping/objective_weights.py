from scheduling.domain import PlanningUnit, PlanningUnitType, SolverObjectiveWeights
from scheduling.timeoffice.reading.objective_weights import TimeOfficeObjectiveWeightRow

OBJECTIVE_FIELDS = set(SolverObjectiveWeights.model_fields) - {"planning_unit_id"}


def map_objective_weights(
    *,
    planning_units: tuple[PlanningUnit, ...],
    rows: tuple[TimeOfficeObjectiveWeightRow, ...],
) -> tuple[SolverObjectiveWeights, ...]:
    selected_station_ids = sorted(
        unit.planning_unit_id for unit in planning_units if unit.type == PlanningUnitType.STATION
    )

    rows_by_planning_unit_id: dict[int, list[TimeOfficeObjectiveWeightRow]] = {
        planning_unit_id: [] for planning_unit_id in selected_station_ids
    }

    for row in rows:
        if row.planning_unit_id in rows_by_planning_unit_id:
            rows_by_planning_unit_id[row.planning_unit_id].append(row)

    return tuple(
        _map_objective_weights_for_planning_unit(
            planning_unit_id=planning_unit_id,
            rows=tuple(rows_by_planning_unit_id[planning_unit_id]),
        )
        for planning_unit_id in selected_station_ids
    )


def _map_objective_weights_for_planning_unit(
    *,
    planning_unit_id: int,
    rows: tuple[TimeOfficeObjectiveWeightRow, ...],
) -> SolverObjectiveWeights:
    values = SolverObjectiveWeights.default_for_planning_unit(planning_unit_id).model_dump()

    for row in rows:
        if row.objective_name not in OBJECTIVE_FIELDS:
            raise ValueError(f"Unknown objective weight field: {row.objective_name!r}.")

        values[row.objective_name] = row.weight

    return SolverObjectiveWeights(**values)
