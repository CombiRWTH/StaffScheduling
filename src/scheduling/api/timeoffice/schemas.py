from typing import Any

from pydantic import Field

from scheduling.domain import PlanningMonth, SchedulingBaseModel


class DBRequest(SchedulingBaseModel):
    planning_unit_id: int
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)

    def planning_month(self) -> PlanningMonth:
        return PlanningMonth(year=self.year, month=self.month)

    solution_data: dict[str, Any] | None = None
