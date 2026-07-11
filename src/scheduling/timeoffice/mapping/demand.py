from datetime import timedelta

from scheduling.domain import DemandRequirement, PlanningMonth, PlanningUnit, PlanningUnitType
from scheduling.domain.employee import StaffLevel
from scheduling.domain.shift import ShiftId
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.reading.demand import TimeOfficeDemandRow

WEEKDAY_INDEX_BY_NAME = {
    "Montag": 0,
    "Dienstag": 1,
    "Mittwoch": 2,
    "Donnerstag": 3,
    "Freitag": 4,
    "Samstag": 5,
    "Sonntag": 6,
}

STAFF_LEVEL_BY_FRONTEND_NAME = {
    "Fachkraft": StaffLevel.PROFESSIONAL,
    "Hilfskraft": StaffLevel.ASSISTANT,
    "Azubi": StaffLevel.TRAINEE,
}

MINIMAL_STAFF_SHIFT_CODES = {"F", "S", "N", "Z"}


def map_demand_requirements(
    *,
    planning_month: PlanningMonth,
    planning_units: tuple[PlanningUnit, ...],
    rows: tuple[TimeOfficeDemandRow, ...],
    facts: TimeOfficeFacts,
) -> tuple[DemandRequirement, ...]:
    selected_station_ids = {unit.planning_unit_id for unit in planning_units if unit.type == PlanningUnitType.STATION}

    requirements: list[DemandRequirement] = []

    for row in rows:
        if row.planning_unit_id not in selected_station_ids:
            continue

        if row.minimum_count <= 0:
            continue

        requirements.extend(
            _expand_demand_row(
                row=row,
                planning_month=planning_month,
                facts=facts,
            )
        )

    return tuple(requirements)


def _expand_demand_row(
    *,
    row: TimeOfficeDemandRow,
    planning_month: PlanningMonth,
    facts: TimeOfficeFacts,
) -> tuple[DemandRequirement, ...]:
    weekday_index = _weekday_index_from_name(row.weekday_name)
    staff_level = _staff_level_from_name(row.staff_level)
    shift_id = _require_minimal_staffing_shift(row.shift_id, facts=facts)

    requirements: list[DemandRequirement] = []

    current_date = planning_month.start
    while current_date <= planning_month.end:
        if current_date.isoweekday() - 1 == weekday_index:
            requirements.append(
                DemandRequirement(
                    planning_unit_id=row.planning_unit_id,
                    date=current_date,
                    shift_id=shift_id,
                    staff_level=staff_level,
                    required_count=row.minimum_count,
                )
            )

        current_date += timedelta(days=1)

    return tuple(requirements)


def _weekday_index_from_name(weekday_name: str) -> int:
    try:
        return WEEKDAY_INDEX_BY_NAME[weekday_name]
    except KeyError as exc:
        raise ValueError(f"Unknown minimal staffing weekday_name={weekday_name!r}.") from exc


def _staff_level_from_name(staff_level: str) -> StaffLevel:
    try:
        return STAFF_LEVEL_BY_FRONTEND_NAME[staff_level]
    except KeyError as exc:
        raise ValueError(f"Unknown minimal staffing staff_level={staff_level!r}.") from exc


def _require_minimal_staffing_shift(
    shift_id: ShiftId,
    *,
    facts: TimeOfficeFacts,
) -> ShiftId:
    shift_fact = facts.reference_shift_facts_by_id.get(shift_id)
    if shift_fact is None:
        raise ValueError(f"Minimal staffing references unknown reference shift_id={shift_id}.")

    if shift_fact.expected_code not in MINIMAL_STAFF_SHIFT_CODES:
        raise ValueError(
            "Minimal staffing references unsupported shift: "
            f"shift_id={shift_id}, expected_code={shift_fact.expected_code!r}."
        )

    return shift_id
