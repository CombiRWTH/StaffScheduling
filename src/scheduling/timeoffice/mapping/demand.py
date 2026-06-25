from datetime import timedelta

from scheduling.domain import DemandRequirement, PlanningMonth, PlanningUnit, PlanningUnitType, StaffingDemandRole
from scheduling.domain.shift import ShiftId
from scheduling.timeoffice.facts import PlanningUnitDemandMatrix, TimeOfficeFacts


def map_demand_requirements(
    *,
    planning_month: PlanningMonth,
    planning_units: tuple[PlanningUnit, ...],
    facts: TimeOfficeFacts,
) -> tuple[DemandRequirement, ...]:
    requirements: list[DemandRequirement] = []

    selected_station_ids = sorted(
        unit.planning_unit_id for unit in planning_units if unit.type == PlanningUnitType.STATION
    )

    for planning_unit_id in selected_station_ids:
        demand_matrix = facts.fallback_demand_by_planning_unit.get(planning_unit_id)
        if demand_matrix is None:
            raise ValueError(
                f"Missing fallback demand matrix for selected station planning_unit_id={planning_unit_id}."
            )

        requirements.extend(
            _expand_planning_unit_demand(
                planning_unit_id=planning_unit_id,
                planning_month=planning_month,
                demand_matrix=demand_matrix,
                facts=facts,
            )
        )

    return tuple(requirements)


def _expand_planning_unit_demand(
    *,
    planning_unit_id: int,
    planning_month: PlanningMonth,
    demand_matrix: PlanningUnitDemandMatrix,
    facts: TimeOfficeFacts,
) -> tuple[DemandRequirement, ...]:
    requirements: list[DemandRequirement] = []

    current_date = planning_month.start
    while current_date <= planning_month.end:
        weekday_index = current_date.isoweekday() - 1

        for staff_level, demand_by_shift_id in demand_matrix.items():
            for shift_id, weekday_demand in demand_by_shift_id.items():
                _validate_weekday_demand(shift_id=shift_id, weekday_demand=weekday_demand)

                _require_minimum_staffing_reference_shift(shift_id=shift_id, facts=facts)

                required_count = weekday_demand[weekday_index]
                if required_count <= 0:
                    continue

                requirements.append(
                    DemandRequirement(
                        planning_unit_id=planning_unit_id,
                        date=current_date,
                        shift_id=shift_id,
                        staff_level=staff_level,
                        required_count=required_count,
                    )
                )

        current_date += timedelta(days=1)

    return tuple(requirements)


def _validate_weekday_demand(*, shift_id: ShiftId, weekday_demand: tuple[int, ...]) -> None:
    if len(weekday_demand) != 7:
        raise ValueError(
            "Fallback demand weekday tuple must contain exactly seven values "
            f"(Mo, Di, Mi, Do, Fr, Sa, So): shift_id={shift_id} values={weekday_demand}."
        )


def _require_minimum_staffing_reference_shift(*, shift_id: ShiftId, facts: TimeOfficeFacts) -> None:
    shift_fact = facts.reference_shift_facts_by_id.get(shift_id)
    if shift_fact is None:
        raise ValueError(f"Fallback demand references non-reference shift_id={shift_id}.")

    if shift_fact.staffing_role != StaffingDemandRole.REQUIRED_MINIMUM:
        raise ValueError(
            "Fallback demand must reference REQUIRED_MINIMUM shifts only: "
            f"shift_id={shift_id} staffing_role={shift_fact.staffing_role}."
        )
