from datetime import date as Date

from scheduling.domain import Shift, Wish, WishType
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.mapping.shifts import reference_shift_id_for_source_shift
from scheduling.timeoffice.reading.wishes import TimeOfficeWishRow


def map_wishes(
    rows: tuple[TimeOfficeWishRow, ...],
    *,
    shifts: tuple[Shift, ...],
    facts: TimeOfficeFacts,
) -> tuple[Wish, ...]:
    known_shift_ids = {shift.shift_id for shift in shifts}

    wishes = tuple(
        _map_wish(
            row=row,
            known_shift_ids=known_shift_ids,
            facts=facts,
        )
        for row in rows
    )

    return _deduplicate_wishes(wishes)


def _map_wish(
    *,
    row: TimeOfficeWishRow,
    known_shift_ids: set[int],
    facts: TimeOfficeFacts,
) -> Wish:
    if row.work_shift_id is not None:
        return _map_preferred_shift_wish(
            row=row,
            known_shift_ids=known_shift_ids,
            facts=facts,
        )

    return _map_absence_wish(row=row, facts=facts)


def _map_preferred_shift_wish(
    *,
    row: TimeOfficeWishRow,
    known_shift_ids: set[int],
    facts: TimeOfficeFacts,
) -> Wish:
    reference_shift_id = reference_shift_id_for_source_shift(
        source_shift_id=row.work_shift_id,
        source_shift_code=row.work_shift_code,
        facts=facts,
        context=(f"TimeOffice preferred-shift wish employee_id={row.employee_id} date={row.wish_date.date()}"),
    )

    if reference_shift_id not in known_shift_ids:
        raise ValueError(
            "TimeOffice preferred-shift wish references shift that is not part "
            "of the mapped SchedulingDataset: "
            f"source_shift_id={row.work_shift_id} "
            f"reference_shift_id={reference_shift_id} "
            f"employee_id={row.employee_id} "
            f"wish_date={row.wish_date}."
        )

    return Wish(
        employee_id=row.employee_id,
        planning_unit_id=row.planning_unit_id,
        date=row.wish_date.date(),
        type=WishType.PREFERRED_SHIFT,
        shift_id=reference_shift_id,
    )


def _map_absence_wish(
    *,
    row: TimeOfficeWishRow,
    facts: TimeOfficeFacts,
) -> Wish:
    absence_shift_id = _resolved_absence_shift_id(row)

    if row.resolved_absence_code is None:
        raise ValueError(
            "Missing resolved absence code for TimeOffice wish row: "
            f"absence_shift_id={absence_shift_id} "
            f"employee_id={row.employee_id} "
            f"wish_date={row.wish_date}."
        )

    wish_type = facts.wish_type_by_absence_code.get(row.resolved_absence_code)
    if wish_type is None:
        raise ValueError(
            "Unmapped TimeOffice wish absence code: "
            f"absence_shift_id={absence_shift_id} "
            f"absence_code={row.resolved_absence_code!r} "
            f"absence_name={row.resolved_absence_name!r}."
        )

    if wish_type in {WishType.FREE_SHIFT, WishType.PREFERRED_SHIFT}:
        raise ValueError(
            "TimeOffice absence wish was mapped to a shift-scoped wish type, "
            "but the current TimeOffice wish row does not provide a canonical "
            "target work shift_id. "
            f"absence_shift_id={absence_shift_id} "
            f"absence_code={row.resolved_absence_code!r} "
            f"wish_type={wish_type}."
        )

    return Wish(
        employee_id=row.employee_id,
        planning_unit_id=row.planning_unit_id,
        date=row.wish_date.date(),
        type=wish_type,
    )


def _resolved_absence_shift_id(row: TimeOfficeWishRow) -> int:
    if row.global_absence_shift_id is not None:
        return row.global_absence_shift_id

    if row.absence_shift_id is not None:
        return row.absence_shift_id

    raise ValueError(
        "Invalid TimeOffice wish row after source-row validation: "
        f"missing absence shift id for employee_id={row.employee_id}, "
        f"wish_date={row.wish_date}."
    )


def _deduplicate_wishes(wishes: tuple[Wish, ...]) -> tuple[Wish, ...]:
    wishes_by_key: dict[tuple[int, int, Date, WishType, int | None], Wish] = {}

    for wish in wishes:
        key = (
            wish.employee_id,
            wish.planning_unit_id,
            wish.date,
            wish.type,
            wish.shift_id,
        )
        wishes_by_key.setdefault(key, wish)

    return tuple(
        wishes_by_key[key]
        for key in sorted(
            wishes_by_key,
            key=lambda item: (
                item[0],
                item[1],
                item[2],
                item[3].value,
                item[4] or -1,
            ),
        )
    )
