from scheduling.api.solve.schemas import SolveOptions
from scheduling.domain.planning_unit import PlanningUnit, PlanningUnitType
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.reading.options import TimeOfficePlanningUnitOptionRow


def map_solve_options(*, rows: tuple[TimeOfficePlanningUnitOptionRow, ...], facts: TimeOfficeFacts) -> SolveOptions:
    rows_by_planning_unit_id = {row.planning_unit_id: row for row in rows}

    planning_units: list[PlanningUnit] = []

    for planning_unit_id, planning_unit_type in sorted(facts.planning_unit_type_by_id.items()):
        if planning_unit_type != PlanningUnitType.STATION:
            continue

        row = rows_by_planning_unit_id.get(planning_unit_id)
        if row is None:
            raise ValueError(
                f"Configured planning unit does not exist in TimeOffice: planning_unit_id={planning_unit_id}."
            )

        planning_units.append(
            PlanningUnit(
                planning_unit_id=planning_unit_id,
                display_name=row.planning_unit_code or f"Planning unit {planning_unit_id}",
                type=planning_unit_type,
            )
        )

    return SolveOptions(planning_units=tuple(planning_units))
