"""Monthly generation jobs: one solve at a time, the latest job kept in memory until the API restarts."""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from enum import StrEnum
from threading import Lock
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import Field

from app.domain import PlanningMonth, PositiveId, SchedulingBaseModel, SchedulingDataset
from app.solver.models import Solution

logger = logging.getLogger(__name__)

# Solver search limits: below the minimum a month of the example size cannot be searched meaningfully;
# the maximum bounds a mistyped value, as real monthly runs stay far below an hour.
MIN_TIMEOUT_SECONDS = 30
MAX_TIMEOUT_SECONDS = 3600

FAILED = "Generation failed unexpectedly; the API log has details."


class GenerationRequest(SchedulingBaseModel):
    """Generate the full planning month for the selected stations within `timeout_seconds` of solver time."""

    planning_unit_ids: tuple[PositiveId, ...] = Field(min_length=1)
    planning_month: PlanningMonth
    timeout_seconds: float = Field(ge=MIN_TIMEOUT_SECONDS, le=MAX_TIMEOUT_SECONDS, allow_inf_nan=False)


class JobState(StrEnum):
    """Where the job is; whether a schedule was found is the solution's status."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationJob(SchedulingBaseModel):
    job_id: UUID
    request: GenerationRequest
    state: JobState
    started_at: datetime
    finished_at: datetime | None = None
    # Set when completed, also if the solver found no schedule; its `check` judges a found schedule.
    solution: Solution | None = None
    # Set when failed.
    error: str | None = None


class GenerationBusy(RuntimeError):
    """Another generation is running; the service solves one at a time."""


class ReadInput(Protocol):
    def __call__(self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth) -> SchedulingDataset: ...


class Solve(Protocol):
    def __call__(self, dataset: SchedulingDataset, timeout: float) -> Solution: ...


class OnSolved(Protocol):
    def __call__(self, dataset: SchedulingDataset, solution: Solution) -> None: ...


class Generation:
    """Start a generation and report the latest job.

    `start` reads and validates the input synchronously, so its errors reach the caller, then solves in
    a background thread and returns the running job at once. Every solution is handed to `on_solved`
    before the job completes. While a job runs, `start` raises `GenerationBusy`. Jobs live in this
    process only: a restart forgets them, and only one API process may run because the lock is process-local.
    """

    def __init__(self, *, read_input: ReadInput, solve: Solve, on_solved: OnSolved) -> None:
        self._read_input = read_input
        self._solve = solve
        self._on_solved = on_solved
        self._lock = Lock()
        self._latest: GenerationJob | None = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="generation")

    def start(self, request: GenerationRequest) -> GenerationJob:
        if not self._lock.acquire(blocking=False):
            raise GenerationBusy("Another generation is running; try again when it has finished.")
        try:
            dataset = self._read_input(
                planning_unit_ids=request.planning_unit_ids, planning_month=request.planning_month
            )
            job = GenerationJob(job_id=uuid4(), request=request, state=JobState.RUNNING, started_at=datetime.now(UTC))
            self._latest = job
            self._executor.submit(self._run, job, dataset)
        except BaseException:
            self._lock.release()
            raise
        logger.info("Generation started: job_id=%s request=%s", job.job_id, request.model_dump(mode="json"))
        return job

    def latest(self) -> GenerationJob | None:
        """The most recent job since the process started, running or finished."""
        return self._latest

    def shutdown(self) -> None:
        """Stop accepting work; a running solve ends with its process.

        No job can be queued behind it: the lock admits one job, which the idle worker starts at once.
        """
        self._executor.shutdown(wait=False, cancel_futures=True)

    def _run(self, job: GenerationJob, dataset: SchedulingDataset) -> None:
        finished = job.model_copy(update={"state": JobState.FAILED, "error": FAILED})
        try:
            solution = self._solve(dataset, job.request.timeout_seconds)
            self._on_solved(dataset, solution)
            finished = job.model_copy(update={"state": JobState.COMPLETED, "solution": solution})
        except Exception:
            logger.exception("Generation failed: job_id=%s", job.job_id)
        finally:
            self._latest = finished.model_copy(update={"finished_at": datetime.now(UTC)})
            self._lock.release()
        logger.info("Generation finished: job_id=%s state=%s", job.job_id, finished.state)
