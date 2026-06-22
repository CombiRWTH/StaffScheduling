import uuid
from datetime import datetime
from enum import StrEnum

from scheduling.domain import PlanningMonth, SchedulingBaseModel
from scheduling.solver.models import Solution


class SolveCommand(SchedulingBaseModel):
    planning_unit_ids: tuple[int, ...]
    planning_month: PlanningMonth


class SolveJobStatus(StrEnum):
    ACCEPTED = "accepted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SolveJob(SchedulingBaseModel):
    job_id: uuid.UUID
    status: SolveJobStatus
    command: SolveCommand
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: Solution | None = None
    error: str | None = None
