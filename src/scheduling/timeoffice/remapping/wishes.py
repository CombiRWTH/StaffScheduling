from datetime import date as Date

from scheduling.domain import SchedulingBaseModel, Wish, WishType
from scheduling.timeoffice.facts import TimeOfficeFacts


class TimeOfficeWishWriteRow(SchedulingBaseModel):
    employee_id: int
    planning_unit_id: int
    plan_id: int
    wish_date: Date
    work_shift_id: int | None = None
    absence_shift_id: int | None = None


PREFERRED_DAY_SHIFT_CODES = ("F", "S", "N")


def map_wishes_to_timeoffice_rows(
    *,
    wishes: tuple[Wish, ...],
    plan_id: int,
    facts: TimeOfficeFacts,
) -> tuple[TimeOfficeWishWriteRow, ...]:
    return tuple(
        row
        for wish in wishes
        for row in _map_wish_to_timeoffice_rows(
            wish=wish,
            plan_id=plan_id,
            facts=facts,
        )
    )


def _map_wish_to_timeoffice_rows(
    *,
    wish: Wish,
    plan_id: int,
    facts: TimeOfficeFacts,
) -> tuple[TimeOfficeWishWriteRow, ...]:
    if wish.type == WishType.PREFERRED_DAY:
        return tuple(
            TimeOfficeWishWriteRow(
                employee_id=wish.employee_id,
                planning_unit_id=wish.planning_unit_id,
                plan_id=plan_id,
                wish_date=wish.date,
                work_shift_id=shift_id,
            )
            for shift_id in _preferred_day_shift_ids(facts)
        )

    if wish.type == WishType.PREFERRED_SHIFT:
        return (
            TimeOfficeWishWriteRow(
                employee_id=wish.employee_id,
                planning_unit_id=wish.planning_unit_id,
                plan_id=plan_id,
                wish_date=wish.date,
                work_shift_id=_require_shift_id(wish),
            ),
        )

    if wish.type == WishType.FREE_DAY:
        return (
            TimeOfficeWishWriteRow(
                employee_id=wish.employee_id,
                planning_unit_id=wish.planning_unit_id,
                plan_id=plan_id,
                wish_date=wish.date,
                absence_shift_id=_absence_shift_id_for_wish_type(wish.type, facts=facts),
            ),
        )

    if wish.type == WishType.FREE_SHIFT:
        return (
            TimeOfficeWishWriteRow(
                employee_id=wish.employee_id,
                planning_unit_id=wish.planning_unit_id,
                plan_id=plan_id,
                wish_date=wish.date,
                work_shift_id=_require_shift_id(wish),
                absence_shift_id=_absence_shift_id_for_wish_type(WishType.FREE_DAY, facts=facts),
            ),
        )

    raise ValueError(f"Unsupported wish type: {wish.type}")


def _preferred_day_shift_ids(facts: TimeOfficeFacts) -> tuple[int, ...]:
    shift_id_by_code = {
        shift_fact.expected_code: shift_id for shift_id, shift_fact in facts.reference_shift_facts_by_id.items()
    }

    return tuple(shift_id_by_code[code] for code in PREFERRED_DAY_SHIFT_CODES)


def _require_shift_id(wish: Wish) -> int:
    if wish.shift_id is None:
        raise ValueError(f"{wish.type} wish requires shift_id.")

    return wish.shift_id


def _absence_shift_id_for_wish_type(wish_type: WishType, *, facts: TimeOfficeFacts) -> int:
    absence_shift_id = facts.wish_absence_shift_id_by_type.get(wish_type)

    if absence_shift_id is None:
        raise ValueError(f"No TimeOffice absence shift configured for wish_type={wish_type}.")

    return absence_shift_id
