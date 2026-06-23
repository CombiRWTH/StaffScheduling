from datetime import date, datetime

from scheduling.domain import Assignment, AssignmentType, Availability, AvailabilityType
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.mapping.shifts import reference_shift_id_for_source_shift
from scheduling.timeoffice.reading.roster import TimeOfficeRosterRow

type AssignmentKey = tuple[int, date, int, AssignmentType, int | None]


def map_assignments(
    *,
    rows: tuple[TimeOfficeRosterRow, ...],
    selected_plan_ids: set[int],
    selected_planning_unit_ids: set[int],
    facts: TimeOfficeFacts,
) -> tuple[Assignment, ...]:
    assignments: list[Assignment] = []
    seen_assignment_keys: set[AssignmentKey] = set()

    for row in rows:
        if row.work_shift_id is None:
            continue

        reference_shift_id = reference_shift_id_for_source_shift(
            source_shift_id=row.work_shift_id,
            source_shift_code=row.work_shift_code,
            facts=facts,
            context=(f"TimeOffice roster work row employee_id={row.employee_id} date={row.roster_date.date()}"),
        )

        assignment_type = _assignment_type(
            plan_id=row.plan_id,
            planning_unit_id=row.planning_unit_id,
            selected_plan_ids=selected_plan_ids,
            selected_planning_unit_ids=selected_planning_unit_ids,
        )

        assignment = Assignment(
            employee_id=row.employee_id,
            date=row.roster_date.date(),
            shift_id=reference_shift_id,
            assignment_type=assignment_type,
            planning_unit_id=(row.planning_unit_id if assignment_type == AssignmentType.PLANNED else None),
        )

        assignment_key = _assignment_key(assignment)
        if assignment_key in seen_assignment_keys:
            continue

        seen_assignment_keys.add(assignment_key)
        assignments.append(assignment)

    return tuple(assignments)


def _assignment_key(assignment: Assignment) -> AssignmentKey:
    return (
        assignment.employee_id,
        assignment.date,
        assignment.shift_id,
        assignment.assignment_type,
        assignment.planning_unit_id,
    )


def map_availability(*, rows: tuple[TimeOfficeRosterRow, ...], facts: TimeOfficeFacts) -> tuple[Availability, ...]:
    return tuple(
        Availability(
            employee_id=row.employee_id,
            date=row.roster_date.date(),
            availability_type=_availability_type_for_absence_code(
                row.resolved_absence_code,
                facts=facts,
                employee_id=row.employee_id,
                roster_date=row.roster_date,
            ),
        )
        for row in rows
        if _has_absence(row)
    )


def _assignment_type(
    *,
    plan_id: int | None,
    planning_unit_id: int | None,
    selected_plan_ids: set[int],
    selected_planning_unit_ids: set[int],
) -> AssignmentType:
    if plan_id in selected_plan_ids and planning_unit_id in selected_planning_unit_ids:
        return AssignmentType.PLANNED

    return AssignmentType.EXTERNAL


def _has_absence(row: TimeOfficeRosterRow) -> bool:
    return row.global_absence_shift_id is not None or row.absence_shift_id is not None


def _availability_type_for_absence_code(
    absence_code: str | None,
    *,
    facts: TimeOfficeFacts,
    employee_id: int,
    roster_date: datetime,
) -> AvailabilityType:
    if absence_code is None:
        raise ValueError(
            "Missing resolved absence code for TimeOffice roster row: "
            f"employee_id={employee_id} roster_date={roster_date}."
        )

    availability_type = facts.availability_type_by_absence_code.get(absence_code)

    if availability_type is None:
        raise ValueError(
            "Unmapped TimeOffice absence code for availability: "
            f"employee_id={employee_id} roster_date={roster_date} "
            f"absence_code={absence_code!r}."
        )

    return availability_type
