from calendar import monthrange
from collections import defaultdict
from dataclasses import dataclass
from datetime import date as Date
from datetime import timedelta

from scheduling.domain import PlanningMonth, Shift, WeeklyWish, Wish, WishType
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.mapping.shifts import reference_shift_id_for_source_shift
from scheduling.timeoffice.reading.wishes import TimeOfficeWishRow


@dataclass(frozen=True, slots=True)
class MappedWishes:
    wishes: tuple[Wish, ...]
    weekly_wishes: tuple[WeeklyWish, ...]


def map_wishes(
    rows: tuple[TimeOfficeWishRow, ...],
    *,
    shifts: tuple[Shift, ...],
    facts: TimeOfficeFacts,
) -> MappedWishes:
    known_shift_ids = {shift.shift_id for shift in shifts}

    wishes = tuple(
        _map_wish(
            row=row,
            known_shift_ids=known_shift_ids,
            facts=facts,
        )
        for row in rows
    )

    wishes = _deduplicate_wishes(wishes)

    return _split_weekly_repeated_wishes(wishes)


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


def _split_weekly_repeated_wishes(wishes: tuple[Wish, ...]) -> MappedWishes:
    wishes_by_key: dict[tuple[int, int, WishType, int | None, int], list[Wish]] = defaultdict(list)

    for wish in wishes:
        key = (
            wish.employee_id,
            wish.planning_unit_id,
            wish.type,
            wish.shift_id,
            wish.date.isoweekday(),  # 1=Mo, 7=So
        )
        wishes_by_key[key].append(wish)

    normal_wishes: list[Wish] = []
    weekly_wishes: list[WeeklyWish] = []

    for grouped_wishes in wishes_by_key.values():
        sorted_wishes = sorted(grouped_wishes, key=lambda wish: wish.date)
        first_wish = sorted_wishes[0]

        if _is_weekly_repeated_in_month(sorted_wishes):
            weekly_wishes.append(
                WeeklyWish(
                    employee_id=first_wish.employee_id,
                    planning_unit_id=first_wish.planning_unit_id,
                    planning_month=PlanningMonth(
                        year=first_wish.date.year,
                        month=first_wish.date.month,
                    ),
                    weekday=first_wish.date.isoweekday(),
                    type=first_wish.type,
                    shift_id=first_wish.shift_id,
                )
            )
        else:
            normal_wishes.extend(sorted_wishes)

    return MappedWishes(
        wishes=_sort_wishes(tuple(normal_wishes)),
        weekly_wishes=_sort_weekly_wishes(tuple(weekly_wishes)),
    )


def _sort_wishes(wishes: tuple[Wish, ...]) -> tuple[Wish, ...]:
    return tuple(
        sorted(
            wishes,
            key=lambda wish: (
                wish.employee_id,
                wish.planning_unit_id,
                wish.date,
                wish.type.value,
                wish.shift_id or -1,
            ),
        )
    )


def _sort_weekly_wishes(weekly_wishes: tuple[WeeklyWish, ...]) -> tuple[WeeklyWish, ...]:
    return tuple(
        sorted(
            weekly_wishes,
            key=lambda wish: (
                wish.employee_id,
                wish.planning_unit_id,
                wish.planning_month.year,
                wish.planning_month.month,
                wish.weekday,
                wish.type.value,
                wish.shift_id or -1,
            ),
        )
    )


def _is_weekly_repeated_in_month(wishes: list[Wish]) -> bool:
    if len(wishes) < 2:
        return False

    dates = {wish.date for wish in wishes}
    first_date = min(dates)

    expected_dates = set(_same_weekday_dates_in_month(first_date))

    return dates == expected_dates


def _same_weekday_dates_in_month(first_date: Date) -> tuple[Date, ...]:
    _, last_day = monthrange(first_date.year, first_date.month)
    current = Date(first_date.year, first_date.month, 1)

    while current.isoweekday() != first_date.isoweekday():
        current += timedelta(days=1)

    dates: list[Date] = []

    while current.month == first_date.month and current.day <= last_day:
        dates.append(current)
        current += timedelta(days=7)

    return tuple(dates)
