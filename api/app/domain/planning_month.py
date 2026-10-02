from calendar import monthrange
from datetime import date, timedelta
from functools import cached_property

from pydantic import Field, computed_field

from app.domain.core import SchedulingBaseModel


class PlanningMonth(SchedulingBaseModel):
    year: int = Field(ge=2000, le=2200)
    month: int = Field(ge=1, le=12)

    @computed_field
    @property
    def start(self) -> date:
        return date(self.year, self.month, 1)

    @computed_field
    @property
    def end(self) -> date:
        return date(
            self.year,
            self.month,
            monthrange(self.year, self.month)[1],
        )

    @cached_property
    def dates(self) -> tuple[date, ...]:
        """Every date of the month in order."""
        return tuple(self.start + timedelta(days=offset) for offset in range(self.end.day))

    def __contains__(self, day: date) -> bool:
        return self.start <= day <= self.end
