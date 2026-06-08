from datetime import date
from typing import Self

from pydantic import BaseModel, model_validator


class PlanningPeriod(BaseModel):
    """Inclusive planning period for a scheduling run."""

    start: date
    end: date

    @model_validator(mode="after")
    def end_must_not_be_before_start(self) -> Self:
        if self.end < self.start:
            raise ValueError("Planning period end date must not be before start date.")
        return self

    @property
    def month_folder(self) -> str:
        """Return the cache month folder for this period."""
        return f"{self.start.month:02d}_{self.start.year}"
