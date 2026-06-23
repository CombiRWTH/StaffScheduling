from datetime import datetime

from scheduling.domain import Wish, WishKind
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.mapping.shifts import reference_shift_id_for_source_shift
from scheduling.timeoffice.reading.wishes import TimeOfficeWishRow


def map_wishes(*, rows: tuple[TimeOfficeWishRow, ...], facts: TimeOfficeFacts) -> tuple[Wish, ...]:
    return tuple(_map_wish(row=row, facts=facts) for row in rows)


def _map_wish(*, row: TimeOfficeWishRow, facts: TimeOfficeFacts) -> Wish:
    if row.work_shift_id is not None:
        return _map_shift_wish(row=row, facts=facts)

    return _map_absence_wish(row=row, facts=facts)


def _map_shift_wish(*, row: TimeOfficeWishRow, facts: TimeOfficeFacts) -> Wish:
    reference_shift_id = reference_shift_id_for_source_shift(
        source_shift_id=row.work_shift_id,
        source_shift_code=row.work_shift_code,
        facts=facts,
        context=(f"TimeOffice wish work row employee_id={row.employee_id} date={row.wish_date.date()}"),
    )

    return Wish(
        employee_id=row.employee_id,
        planning_unit_id=row.planning_unit_id,
        date=row.wish_date.date(),
        kind=WishKind.SHIFT,
        shift_id=reference_shift_id,
    )


def _map_absence_wish(*, row: TimeOfficeWishRow, facts: TimeOfficeFacts) -> Wish:
    return Wish(
        employee_id=row.employee_id,
        planning_unit_id=row.planning_unit_id,
        date=row.wish_date.date(),
        kind=_wish_kind_for_absence_code(
            row.resolved_absence_code,
            facts=facts,
            employee_id=row.employee_id,
            wish_date=row.wish_date,
        ),
    )


def _wish_kind_for_absence_code(
    absence_code: str | None,
    *,
    facts: TimeOfficeFacts,
    employee_id: int,
    wish_date: datetime,
) -> WishKind:
    if absence_code is None:
        raise ValueError(
            f"Missing resolved absence code for TimeOffice wish row: employee_id={employee_id} wish_date={wish_date}."
        )

    wish_kind = facts.wish_kind_by_absence_code.get(absence_code)
    if wish_kind is None:
        raise ValueError(
            "Unmapped TimeOffice absence code for wish: "
            f"employee_id={employee_id} wish_date={wish_date} "
            f"absence_code={absence_code!r}."
        )

    return wish_kind
