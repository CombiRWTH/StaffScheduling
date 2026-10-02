"""Where a duty lies in real time: Europe/Berlin local shift times turned into UTC instants."""

from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from datetime import date as Date
from functools import cache
from zoneinfo import ZoneInfo

from app.domain.shift import Shift

PLANNING_TIMEZONE = ZoneInfo("Europe/Berlin")


@dataclass(frozen=True, slots=True)
class DutyTimes:
    """The UTC instants of one duty and its work segments; elapsed minutes follow daylight-saving changes."""

    start: datetime
    end: datetime
    work: tuple[tuple[datetime, datetime], ...]

    @property
    def work_minutes(self) -> int:
        """Elapsed active work, excluding breaks; not the paid minutes of the account."""
        return sum(_minutes(end - start) for start, end in self.work)

    @property
    def breaks(self) -> tuple[int, ...]:
        """Lengths in minutes of the gaps between consecutive work segments."""
        return tuple(_minutes(b[0] - a[1]) for a, b in zip(self.work, self.work[1:], strict=False))

    def minutes_until(self, later: DutyTimes) -> int:
        """Elapsed minutes from this duty's end to `later`'s start; negative when they overlap."""
        return _minutes(later.start - self.end)

    def touches(self, day: Date) -> bool:
        """Whether the duty overlaps the local calendar day from 00:00 to 24:00."""
        start, end = day_bounds(day)
        return self.start < end and start < self.end


def duty_times(day: Date, shift: Shift) -> DutyTimes:
    """The duty of `shift` starting on `day`; raises ValueError for local times a clock change skips or repeats."""
    work = tuple((local_instant(day, s.start_minute), local_instant(day, s.end_minute)) for s in shift.segments)
    return DutyTimes(start=work[0][0], end=work[-1][1], work=work)


@cache
def day_bounds(day: Date) -> tuple[datetime, datetime]:
    """The UTC instants of local midnight starting and ending `day`."""
    return local_instant(day, 0), local_instant(day + timedelta(days=1), 0)


def local_instant(day: Date, minute: int) -> datetime:
    """The UTC instant `minute` local minutes after midnight of `day`, refusing ambiguous or skipped times."""
    local = datetime.combine(day, time()) + timedelta(minutes=minute)
    earlier = local.replace(tzinfo=PLANNING_TIMEZONE)
    if earlier.utcoffset() != local.replace(tzinfo=PLANNING_TIMEZONE, fold=1).utcoffset():
        raise ValueError(f"Local time {local:%Y-%m-%d %H:%M} is skipped or repeated by a Europe/Berlin clock change.")
    return earlier.astimezone(UTC)


def _minutes(delta: timedelta) -> int:
    return int(delta.total_seconds() // 60)
