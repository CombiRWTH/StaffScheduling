"""The planning calendar: Europe/Berlin dates with North Rhine-Westphalia public holidays."""

from datetime import date as Date
from datetime import timedelta
from enum import StrEnum
from functools import cache

import holidays
from pydantic import Field

from app.domain.core import SchedulingBaseModel
from app.domain.planning_month import PlanningMonth


class DayType(StrEnum):
    """Which row of a weekly pattern a date takes; a public holiday takes the holiday row."""

    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"
    HOLIDAY = "holiday"


class CalendarDay(SchedulingBaseModel):
    date: Date
    weekday: int = Field(ge=1, le=7)
    """ISO weekday, Monday=1 to Sunday=7; it stays the actual weekday on a public holiday."""
    public_holiday: str | None = None

    @property
    def day_type(self) -> DayType:
        if self.public_holiday:
            return DayType.HOLIDAY
        return list(DayType)[self.weekday - 1]


def public_holiday(day: Date) -> str | None:
    """The German name of the NRW public holiday on `day`, if it is one."""
    return _nrw_holidays(day.year).get(day)


def is_working_day(day: Date) -> bool:
    """A Werktag in the sense of the ArbZG: Monday to Saturday, unless a public holiday."""
    return day.isoweekday() <= 6 and public_holiday(day) is None


def dates_between(start: Date, end: Date) -> tuple[Date, ...]:
    """Every date from `start` to `end`, both inclusive."""
    return tuple(start + timedelta(days=offset) for offset in range((end - start).days + 1))


def month_calendar(month: PlanningMonth) -> tuple[CalendarDay, ...]:
    """Every date of the month with its weekday and NRW public holiday name."""
    return tuple(
        CalendarDay(date=day, weekday=day.isoweekday(), public_holiday=public_holiday(day)) for day in month.dates
    )


@cache
def _nrw_holidays(year: int) -> dict[Date, str]:
    return dict(holidays.country_holidays("DE", subdiv="NW", years=year, language="de"))
