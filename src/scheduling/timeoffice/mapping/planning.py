from scheduling.domain import Plan, PlanningUnit, PlanningUnitType
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.reading.planning_units import TimeOfficePlanningUnitRow


def map_planning_units(
    rows: tuple[TimeOfficePlanningUnitRow, ...], *, facts: TimeOfficeFacts
) -> tuple[PlanningUnit, ...]:
    return tuple(
        PlanningUnit(
            planning_unit_id=row.planning_unit_id,
            display_name=f"Planning Unit {row.planning_unit_id}",
            type=_planning_unit_type(row.planning_unit_id, facts=facts),
        )
        for row in rows
    )


def map_plans(rows: tuple[TimeOfficePlanningUnitRow, ...]) -> tuple[Plan, ...]:
    return tuple(
        Plan(
            plan_id=row.plan_id,
            planning_unit_id=row.plan_planning_unit_id,
        )
        for row in rows
    )


def _planning_unit_type(planning_unit_id: int, *, facts: TimeOfficeFacts) -> PlanningUnitType:
    type = facts.planning_unit_type_by_id.get(planning_unit_id)

    if type is None:
        raise ValueError(f"No PlanningUnitType configured for TimeOffice planning_unit_id={planning_unit_id}.")

    return type
