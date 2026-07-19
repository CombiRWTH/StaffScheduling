from datetime import date as Date

from scheduling.domain import Availability, AvailabilityType
from scheduling.domain.core import SchedulingBaseModel
from scheduling.timeoffice.facts import TimeOfficeFacts


class TimeOfficeAvailabilityWriteRow(SchedulingBaseModel):
    employee_id: int
    plan_id: int
    planning_unit_id: int
    availability_date: Date
    work_shift_id: int | None = None
    absence_shift_id: int


def map_availabilities_to_timeoffice_rows(
    *,
    availabilities: tuple[Availability, ...],
    plan_id: int,
    planning_unit_id: int,
    facts: TimeOfficeFacts,
) -> tuple[TimeOfficeAvailabilityWriteRow, ...]:
    rows: list[TimeOfficeAvailabilityWriteRow] = []

    for availability in availabilities:
        absence_shift_id = _absence_shift_id_for_availability_type(
            availability.availability_type,
            facts=facts,
        )

        if availability.shift_ids is None:
            rows.append(
                TimeOfficeAvailabilityWriteRow(
                    employee_id=availability.employee_id,
                    plan_id=plan_id,
                    planning_unit_id=planning_unit_id,
                    availability_date=availability.date,
                    work_shift_id=None,
                    absence_shift_id=absence_shift_id,
                )
            )
            continue

        for shift_id in availability.shift_ids:
            rows.append(
                TimeOfficeAvailabilityWriteRow(
                    employee_id=availability.employee_id,
                    plan_id=plan_id,
                    planning_unit_id=planning_unit_id,
                    availability_date=availability.date,
                    work_shift_id=shift_id,
                    absence_shift_id=absence_shift_id,
                )
            )

    return tuple(rows)


def _absence_shift_id_for_availability_type(
    availability_type: AvailabilityType,
    *,
    facts: TimeOfficeFacts,
) -> int:
    absence_shift_id = facts.availability_absence_shift_id_by_type.get(availability_type)

    if absence_shift_id is None:
        raise ValueError(f"No TimeOffice absence shift configured for availability_type={availability_type}.")

    return absence_shift_id
