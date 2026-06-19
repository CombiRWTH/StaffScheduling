import uuid
from datetime import datetime
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from scheduling.api.types import ApiDate
from scheduling.domain import SchedulingBaseModel
from scheduling.domain.dataset import PlanningPeriod
from scheduling.solver.tmp import SolverResult


class SolveJobStatus(StrEnum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SolveRequest(SchedulingBaseModel):
    planning_unit_ids: tuple[int, ...]
    start: ApiDate
    end: ApiDate

    @model_validator(mode="after")
    def validate_request(self) -> Self:
        if not self.planning_unit_ids:
            raise ValueError("At least one planning unit id is required.")

        return self


class SolveCommand(SchedulingBaseModel):
    planning_unit_ids: tuple[int, ...]
    period: PlanningPeriod


class SolveAcceptedResponse(SchedulingBaseModel):
    job_id: uuid.UUID
    status: SolveJobStatus


class SolveJob(SchedulingBaseModel):
    job_id: uuid.UUID
    status: SolveJobStatus
    command: SolveCommand
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: SolverResult | None = None
    error: str | None = None
