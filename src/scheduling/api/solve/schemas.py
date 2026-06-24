import uuid
from typing import Self

from pydantic import Field, model_validator

from scheduling.api.solve.job_models import SolveJobStatus
from scheduling.domain import PlanningMonth, PlanningUnit, SchedulingBaseModel


class SolveOptions(SchedulingBaseModel):
    planning_units: tuple[PlanningUnit, ...]


class SolveRequest(SchedulingBaseModel):
    planning_unit_ids: tuple[int, ...]
    year: int = Field(ge=2000, le=2100)
    month: int = Field(ge=1, le=12)

    def planning_month(self) -> PlanningMonth:
        return PlanningMonth(year=self.year, month=self.month)

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if not self.planning_unit_ids:
            raise ValueError("At least one planning unit id is required.")

        return self


class SolveAcceptedResponse(SchedulingBaseModel):
    job_id: uuid.UUID
    status: SolveJobStatus
