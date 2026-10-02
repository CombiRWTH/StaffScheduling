"""Small canonical scheduling inputs for the schedule check and solver tests."""

from collections.abc import Iterable
from datetime import date, timedelta

from app.domain import (
    POLICY,
    Assignment,
    Availability,
    AvailabilityType,
    DemandRequirement,
    Employee,
    MonthlyWorkAccount,
    PlanningMonth,
    PlanningUnit,
    PlanningUnitMembership,
    PlanningUnitType,
    ScheduleContext,
    SchedulingDataset,
    Shift,
    ShiftType,
    StaffLevel,
    Wish,
    WorkCredit,
    WorkSegment,
)

JANUARY = PlanningMonth(year=2026, month=1)
NORTH, SOUTH, JUMPER_POOL = 101, 102, 201
UNITS = (
    PlanningUnit(planning_unit_id=NORTH, display_name="North", type=PlanningUnitType.STATION),
    PlanningUnit(planning_unit_id=SOUTH, display_name="South", type=PlanningUnitType.STATION),
    PlanningUnit(planning_unit_id=JUMPER_POOL, display_name="Jumper pool", type=PlanningUnitType.JUMPER_POOL),
)


def shift(shift_id: int, code: str, kind: ShiftType, *segments: tuple[int, int]) -> Shift:
    """A shift of work segments in local minutes after midnight; paid minutes equal the work."""
    return Shift(
        shift_id=shift_id,
        code=code,
        type=kind,
        segments=tuple(WorkSegment(start_minute=start, end_minute=end) for start, end in segments),
        net_work_minutes=sum(end - start for start, end in segments),
    )


def hm(hours: int, minutes: int = 0, *, next_day: bool = False) -> int:
    return (24 if next_day else 0) * 60 + hours * 60 + minutes


# The prepared reference catalog: early 05:55-13:25, intermediate 08:30-14:15, late 13:15-21:00, night 20:10-06:10.
EARLY = shift(1113, "F", ShiftType.EARLY, (hm(5, 55), hm(10)), (hm(10, 30), hm(13, 25)))
INTERMEDIATE = shift(1453, "Z", ShiftType.INTERMEDIATE, (hm(8, 30), hm(14, 15)))
LATE = shift(1605, "S", ShiftType.LATE, (hm(13, 15), hm(16)), (hm(16, 30), hm(21)))
NIGHT = shift(
    1690,
    "N",
    ShiftType.NIGHT,
    (hm(20, 10), hm(21, 45)),
    (hm(22), hm(24)),
    (hm(0, 30, next_day=True), hm(6, 10, next_day=True)),
)
CATALOG = (EARLY, INTERMEDIATE, LATE, NIGHT)


def member(
    employee_id: int,
    level: StaffLevel = StaffLevel.PROFESSIONAL,
    *,
    home: int = NORTH,
    replacements: Iterable[int] = (),
) -> tuple[PlanningUnitMembership, ...]:
    """A home membership (jumper pool or station) plus replacement memberships at stations."""
    return tuple(
        PlanningUnitMembership(
            planning_unit_id=unit,
            employee_id=employee_id,
            valid_from=date(2025, 12, 1),
            valid_until=date(2026, 12, 31),
            staff_level=level,
            is_home=unit == home,
            is_replacement=unit != home,
        )
        for unit in (home, *replacements)
    )


def account(employee_id: int, target: int, credits: int = 0, month: PlanningMonth = JANUARY) -> MonthlyWorkAccount:
    details = (
        (WorkCredit(date=month.start, minutes=credits, kind="approved_absence", source="Example vacation"),)
        if credits
        else ()
    )
    return MonthlyWorkAccount(employee_id=employee_id, target_minutes=target, credit_details=details)


def need(day: date, shift_: Shift, count: int = 1, level: StaffLevel = StaffLevel.PROFESSIONAL, unit: int = NORTH):
    return DemandRequirement(
        planning_unit_id=unit, date=day, shift_id=shift_.shift_id, staff_level=level, required_count=count
    )


def duty(
    employee_id: int,
    day: date,
    shift_: Shift,
    *,
    unit: int = NORTH,
    level: StaffLevel = StaffLevel.PROFESSIONAL,
) -> Assignment:
    return Assignment(
        employee_id=employee_id, date=day, planning_unit_id=unit, shift_id=shift_.shift_id, staff_level=level
    )


def away(
    employee_id: int,
    day: date,
    kind: AvailabilityType = AvailabilityType.VACATION,
    shift_ids: tuple[int, ...] | None = None,
) -> Availability:
    return Availability(employee_id=employee_id, date=day, availability_type=kind, shift_ids=shift_ids)


def jan(day: int) -> date:
    return date(2026, 1, day)


def dataset(
    *,
    memberships: Iterable[PlanningUnitMembership],
    accounts: Iterable[MonthlyWorkAccount],
    demand: Iterable[DemandRequirement] = (),
    availability: Iterable[Availability] = (),
    wishes: Iterable[Wish] = (),
    shifts: Iterable[Shift] = CATALOG,
    month: PlanningMonth = JANUARY,
    context_duties: Iterable[Assignment] = (),
    context_availability: Iterable[Availability] = (),
    covered_days_before: int = 14,
    covered_days_after: int = 0,
    levels: dict[int, StaffLevel] | None = None,
) -> SchedulingDataset:
    """A month whose preceding 14 days are trusted context by default, without following context."""
    memberships = tuple(memberships)
    employee_ids = sorted({row.employee_id for row in memberships})
    return SchedulingDataset(
        planning_month=month,
        planning_units=UNITS,
        shifts=tuple(shifts),
        demand_requirements=tuple(demand),
        employees=tuple(
            Employee(
                employee_id=employee_id,
                display_name=f"Example {employee_id}",
                staff_level=(levels or {}).get(employee_id, StaffLevel.PROFESSIONAL),
            )
            for employee_id in employee_ids
        ),
        planning_unit_memberships=memberships,
        availability=tuple(availability),
        wishes=tuple(wishes),
        monthly_work_accounts=tuple(accounts),
        context=ScheduleContext(
            covered_from=month.start - timedelta(days=covered_days_before),
            covered_until=month.end + timedelta(days=covered_days_after),
            duties=tuple(context_duties),
            availability=tuple(context_availability),
        ),
    )


APRIL = PlanningMonth(year=2026, month=4)


def alone(
    context: Iterable[Assignment] = (),
    month: PlanningMonth = JANUARY,
    *,
    before: int = POLICY.preceding_context_days,
    after: int = 0,
) -> SchedulingDataset:
    """One North professional with a zero target and the policy's preceding context days."""
    return dataset(
        memberships=member(1),
        accounts=[account(1, 0, month=month)],
        month=month,
        context_duties=context,
        covered_days_before=before,
        covered_days_after=after,
    )


# One employee's schedules with their isolated workdays: (dataset, schedule, events).
ISOLATED_WORKDAYS = (
    # A two-day block is not isolated; the later single day is.
    (alone(), (duty(1, jan(13), EARLY), duty(1, jan(14), EARLY), duty(1, jan(20), LATE)), 1),
    (alone(), (duty(1, jan(1), EARLY),), 1),
    # The trusted duty of December 31 keeps January 1 from being isolated.
    (alone([duty(1, date(2025, 12, 31), EARLY)]), (duty(1, jan(1), EARLY),), 0),
    # A single night counts, although the recovery keeps the next day free.
    (alone(), (duty(1, jan(14), NIGHT),), 1),
    # Without context a month edge is never free: neither January 1 nor January 31 is isolated.
    (alone(before=0), (duty(1, jan(1), EARLY),), 0),
    (alone(), (duty(1, jan(31), EARLY),), 0),
    (alone(after=POLICY.following_context_days), (duty(1, jan(31), EARLY),), 1),
)

# One employee's schedules with their back-to-back worked weekends: (dataset, schedule, events).
# January 2026 starts on a Thursday: weekends are 3/4, 10/11, 17/18, 24/25 and 31/February 1.
BACK_TO_BACK_WEEKENDS = (
    (alone(), (duty(1, jan(10), EARLY), duty(1, jan(18), LATE)), 1),
    (alone(), (duty(1, jan(10), EARLY), duty(1, jan(17), EARLY), duty(1, jan(24), EARLY)), 2),
    # Two free weekends in a row are no event.
    (alone(), (duty(1, jan(10), EARLY), duty(1, jan(24), EARLY)), 0),
    # A Friday night touches its Saturday.
    (alone(), (duty(1, jan(9), NIGHT), duty(1, jan(17), EARLY)), 1),
    # The earlier weekend of January 4 has its Friday six days before the month: not counted, even
    # with more trusted context.
    (alone([duty(1, date(2025, 12, 27), EARLY)], before=14), (duty(1, jan(3), EARLY),), 0),
    # April 2026 starts on a Wednesday: the Friday night of March 27 lies in the five preceding days.
    (alone([duty(1, date(2026, 3, 27), NIGHT)], APRIL), (duty(1, date(2026, 4, 4), EARLY),), 1),
)
