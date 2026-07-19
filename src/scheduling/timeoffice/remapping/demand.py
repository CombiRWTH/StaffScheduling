from scheduling.domain import DemandRequirement
from scheduling.domain.core import SchedulingBaseModel
from scheduling.domain.employee import StaffLevel


class TimeOfficeMinimalStaffingWriteRow(SchedulingBaseModel):
    planning_unit_id: int
    weekday_name: str
    staff_level: str
    shift_id: int
    minimum_count: int


WEEKDAY_NAME_BY_ISO_WEEKDAY = {
    1: "Montag",
    2: "Dienstag",
    3: "Mittwoch",
    4: "Donnerstag",
    5: "Freitag",
    6: "Samstag",
    7: "Sonntag",
}

STAFF_LEVEL_NAME_BY_DOMAIN = {
    StaffLevel.PROFESSIONAL: "Fachkraft",
    StaffLevel.ASSISTANT: "Hilfskraft",
    StaffLevel.TRAINEE: "Azubi",
}


def map_demand_requirements_to_minimal_staffing_rows(
    demand_requirements: tuple[DemandRequirement, ...],
) -> tuple[TimeOfficeMinimalStaffingWriteRow, ...]:
    rows_by_key: dict[tuple[int, str, str, int], int] = {}

    for requirement in demand_requirements:
        weekday_name = WEEKDAY_NAME_BY_ISO_WEEKDAY[requirement.date.isoweekday()]
        staff_level = STAFF_LEVEL_NAME_BY_DOMAIN[requirement.staff_level]

        key = (
            requirement.planning_unit_id,
            weekday_name,
            staff_level,
            requirement.shift_id,
        )

        existing_count = rows_by_key.get(key)
        if existing_count is not None and existing_count != requirement.required_count:
            raise ValueError(
                "Conflicting minimal staffing values for same planning_unit/weekday/staff_level/shift: "
                f"key={key}, existing={existing_count}, new={requirement.required_count}."
            )

        rows_by_key[key] = requirement.required_count

    return tuple(
        TimeOfficeMinimalStaffingWriteRow(
            planning_unit_id=planning_unit_id,
            weekday_name=weekday_name,
            staff_level=staff_level,
            shift_id=shift_id,
            minimum_count=minimum_count,
        )
        for (planning_unit_id, weekday_name, staff_level, shift_id), minimum_count in sorted(rows_by_key.items())
    )
