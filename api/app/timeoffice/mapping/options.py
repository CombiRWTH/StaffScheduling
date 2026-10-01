from app.domain.planning_unit import PlanningUnit, PlanningUnitType
from app.routers.solve.schemas import SolveOptions
from app.timeoffice.facts import TimeOfficeFacts
from app.timeoffice.reading.options import TimeOfficePlanningUnitOptionRow


def map_planning_units(
    *, rows: tuple[TimeOfficePlanningUnitOptionRow, ...], facts: TimeOfficeFacts
) -> tuple[PlanningUnit, ...]:
    if len({row.planning_unit_id for row in rows}) != len(rows):
        raise ValueError("Duplicate planning unit option rows.")
    if not set(facts.planning_unit_type_by_id) <= {row.planning_unit_id for row in rows}:
        raise ValueError("Configured planning units are missing.")
    if any(not row.planning_unit_code for row in rows):
        raise ValueError("Planning unit display names are missing.")
    return tuple(
        PlanningUnit(
            planning_unit_id=row.planning_unit_id,
            display_name=row.planning_unit_code,
            type=facts.planning_unit_type_by_id[row.planning_unit_id],
        )
        for row in rows
        if row.planning_unit_id in facts.planning_unit_type_by_id and row.planning_unit_code is not None
    )


def map_solve_options(*, rows: tuple[TimeOfficePlanningUnitOptionRow, ...], facts: TimeOfficeFacts) -> SolveOptions:
    units = map_planning_units(rows=rows, facts=facts)
    return SolveOptions(planning_units=tuple(unit for unit in units if unit.type == PlanningUnitType.STATION))
