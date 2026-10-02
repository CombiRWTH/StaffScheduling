"""The planning calendar: Europe/Berlin dates with North Rhine-Westphalia public holidays."""

from datetime import date as Date
from datetime import timedelta
from enum import StrEnum

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
    # ISO weekday, Monday=1 to Sunday=7; it stays the actual weekday on a public holiday.
    weekday: int = Field(ge=1, le=7)
    public_holiday: str | None = None

    @property
    def day_type(self) -> DayType:
        if self.public_holiday:
            return DayType.HOLIDAY
        return list(DayType)[self.weekday - 1]


def month_calendar(month: PlanningMonth) -> tuple[CalendarDay, ...]:
    """Every date of the month with its weekday and NRW public holiday name."""
    names = holidays.country_holidays("DE", subdiv="NW", years=month.year, language="de")
    days = (month.start + timedelta(days=offset) for offset in range((month.end - month.start).days + 1))
    return tuple(CalendarDay(date=day, weekday=day.isoweekday(), public_holiday=names.get(day)) for day in days)
