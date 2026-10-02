"""The hard-rule policy of the ordinary adult baseline.

The solver and the independent schedule check each implement the rules on their own; they share
only this policy and the duty times of `app.domain.duty`.
"""

from datetime import date as Date

from app.domain.availability import AvailabilityType
from app.domain.calendar import public_holiday
from app.domain.core import SchedulingBaseModel

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
    # ArbZG §3/§6(2): at most ten hours of work a day, and every month at most eight hours per
    # Werktag on average. Each month is its own compensation period, so every longer one holds too.
    max_daily_work_minutes: int = 10 * 60
    average_daily_work_minutes: int = 8 * 60
    # ArbZG §4: breaks by active work, counted in parts of at least 15 minutes.
    short_break_after_minutes: int = 6 * 60
    short_break_minutes: int = 30
    long_break_after_minutes: int = 9 * 60
    long_break_minutes: int = 45
    min_break_part_minutes: int = 15
    max_uninterrupted_work_minutes: int = 6 * 60
    # ArbZG §11(3): a replacement rest day within two weeks (Sunday) or eight weeks (holiday) around
    # the day. A month grants it among its own dates, so no replacement day is claimed by two months.
    sunday_replacement_days: int = 13
    holiday_replacement_days: int = 55
    # Trusted duties a month needs around it: a six-day window ending on its first date reaches five
    # dates back; a final night on its last date reaches three dates ahead through the recovery.
    preceding_context_days: int = 5
    following_context_days: int = 3

    def replacement_days(self, day: Date) -> int | None:
        """How many days around `day` its work may be compensated; None unless a Sunday or Werktag holiday."""
        if day.isoweekday() == 7:
            return self.sunday_replacement_days
        if public_holiday(day) is not None:
            return self.holiday_replacement_days
        return None


POLICY = RulePolicy()
