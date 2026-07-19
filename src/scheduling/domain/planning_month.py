from calendar import monthrange
from datetime import date

from pydantic import Field, computed_field

from scheduling.domain import SchedulingBaseModel


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

    @property
    def label(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"
