"""The hard-rule policy of the ordinary adult baseline and the pure per-duty rule checks.

The solver and the independent schedule check share these small functions over real duty times;
each does its own counting, sequencing and accounting over whole schedules.
"""

from collections.abc import Mapping, Sequence
from datetime import date as Date
from datetime import timedelta

from app.domain.availability import AvailabilityEntry, AvailabilityType
from app.domain.calendar import public_holiday
from app.domain.core import SchedulingBaseModel
from app.domain.duty import DutyTimes
from app.domain.shift import Shift, ShiftType

# Availability that keeps an employee off duty for the whole date.
BLOCKING_AVAILABILITY = frozenset(
    {AvailabilityType.UNAVAILABLE, AvailabilityType.VACATION, AvailabilityType.TRAINING, AvailabilityType.FREE_DAY}
)
# Approved free dates that no night duty may directly precede (problem statement).
APPROVED_FREE = frozenset({AvailabilityType.VACATION, AvailabilityType.FREE_DAY})


class RulePolicy(SchedulingBaseModel):
    """Hard-rule parameters of the ordinary adult baseline; no hospital or AVR exception is selected.

    Every run reports the policy it used. Sources: ArbZG §§3-6 and 11 for work, breaks, rest and
    replacement rest; BAuA night-work guidance, adopted as project policy, for nights and recovery;
    the problem statement for the monthly balance of ±7.67 hours.
    """

    balance_tolerance_minutes: int = 460
    min_rest_minutes: int = 11 * 60
    max_consecutive_nights: int = 3
    night_recovery_minutes: int = 48 * 60
    # ArbZG §3/§6(2): eight hours; up to ten only while the month's average stays at eight per Werktag.
    daily_work_minutes: int = 8 * 60
    extended_daily_work_minutes: int = 10 * 60
    # ArbZG §4: breaks by active work, counted in parts of at least 15 minutes.
    short_break_after_minutes: int = 6 * 60
    short_break_minutes: int = 30
    long_break_after_minutes: int = 9 * 60
    long_break_minutes: int = 45
    min_break_part_minutes: int = 15
    max_uninterrupted_work_minutes: int = 6 * 60
    # ArbZG §11(3): a replacement rest day within two weeks (Sunday) or eight weeks (holiday) around the day.
    sunday_replacement_days: int = 13
    holiday_replacement_days: int = 55
    # Days of trusted duties a month needs before its first date: a night three days earlier still
    # reaches it through the 48-hour recovery, and three earlier nights decide whether a fourth follows.
    preceding_context_days: int = 3


POLICY = RulePolicy()


def duty_problem(times: DutyTimes, policy: RulePolicy = POLICY) -> str | None:
    """Why a duty's own work and break pattern breaks the daily rules, if it does."""
    work = times.work_minutes
    if work > policy.extended_daily_work_minutes:
        return f"{work} minutes of work exceed the daily maximum of {policy.extended_daily_work_minutes}."
    required = (
        policy.long_break_minutes
        if work > policy.long_break_after_minutes
        else policy.short_break_minutes
        if work > policy.short_break_after_minutes
        else 0
    )
    qualifying = sum(gap for gap in times.breaks if gap >= policy.min_break_part_minutes)
    if qualifying < required:
        return f"{work} minutes of work need {required} minutes of break, the duty has {qualifying}."
    # A gap shorter than a qualifying break part does not interrupt the work around it.
    run = 0
    for (start, end), gap in zip(times.work, (*times.breaks, None), strict=True):
        run += int((end - start).total_seconds() // 60)
        if run > policy.max_uninterrupted_work_minutes:
            return f"More than {policy.max_uninterrupted_work_minutes} minutes of work without a break."
        if gap is None or gap >= policy.min_break_part_minutes:
            run = 0
    return None


def rest_conflict(earlier: DutyTimes, later: DutyTimes, policy: RulePolicy = POLICY) -> bool:
    """Whether two duties of one employee overlap or leave less than the minimum rest between them."""
    first, second = sorted((earlier, later), key=lambda times: times.start)
    return first.minutes_until(second) < policy.min_rest_minutes


def availability_problem(
    day: Date, shift: Shift, times: DutyTimes, availability: Mapping[Date, Sequence[AvailabilityEntry]]
) -> str | None:
    """Why the employee's approved availability forbids this duty, if it does.

    A duty is blocked by an unavailable date it touches, by every allowed-shift restriction of its
    start date that omits its shift (several restrictions narrow, never widen), and, as a night duty,
    by an approved vacation or free day on the next date.
    """
    for entry in availability.get(day, ()):
        if entry.availability_type == AvailabilityType.AVAILABLE_ONLY and shift.shift_id not in (entry.shift_ids or ()):
            return f"Only other shifts are allowed on {day}."
    next_day = day + timedelta(days=1)
    for touched in (day, next_day):
        if touched == day or times.touches(touched):
            for entry in availability.get(touched, ()):
                if entry.availability_type in BLOCKING_AVAILABILITY:
                    return f"The duty overlaps {entry.availability_type.value} on {touched}."
    if shift.type == ShiftType.NIGHT and any(
        entry.availability_type in APPROVED_FREE for entry in availability.get(next_day, ())
    ):
        return f"A night duty may not precede the approved free day {next_day}."
    return None


def replacement_window_days(day: Date, policy: RulePolicy = POLICY) -> int | None:
    """How many days around `day` its work may be compensated by a replacement rest day.

    Sundays and public holidays on a Werktag require one; other days do not.
    """
    if day.isoweekday() == 7:
        return policy.sunday_replacement_days
    if public_holiday(day) is not None:
        return policy.holiday_replacement_days
    return None
