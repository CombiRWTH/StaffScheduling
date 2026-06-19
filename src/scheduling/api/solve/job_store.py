import uuid
from datetime import UTC, datetime

from scheduling.api.solve.schemas import SolveCommand, SolveJob, SolveJobStatus
from scheduling.solver.tmp import SolverResult


class InMemorySolveJobStore:
    """Process-local in-memory solve job store.

    This is intentionally API runtime state. It is not shared across multiple
    Uvicorn workers and should be replaced by persistent storage if needed.
    """

    def __init__(self) -> None:
        self._jobs: dict[uuid.UUID, SolveJob] = {}

    def create(self, command: SolveCommand) -> SolveJob:
        job = SolveJob(
            job_id=uuid.uuid4(),
            status=SolveJobStatus.ACCEPTED,
            command=command,
            created_at=datetime.now(UTC),
        )
        self._jobs[job.job_id] = job
        return job

    def get(self, job_id: uuid.UUID) -> SolveJob | None:
        return self._jobs.get(job_id)

    def mark_running(self, job_id: uuid.UUID) -> SolveJob:
        return self._update(
            job_id,
            status=SolveJobStatus.RUNNING,
            started_at=datetime.now(UTC),
            error=None,
        )

    def mark_succeeded(self, job_id: uuid.UUID, result: SolverResult) -> SolveJob:
        return self._update(
            job_id,
            status=SolveJobStatus.SUCCEEDED,
            finished_at=datetime.now(UTC),
            result=result,
            error=None,
        )

    def mark_failed(self, job_id: uuid.UUID, error: str) -> SolveJob:
        return self._update(
            job_id,
            status=SolveJobStatus.FAILED,
            finished_at=datetime.now(UTC),
            error=error,
        )

    def _update(self, job_id: uuid.UUID, **values: object) -> SolveJob:
        job = self._jobs.get(job_id)

        if job is None:
            raise KeyError(f"Solve job not found: {job_id}")

        updated = job.model_copy(update=values)
        self._jobs[job_id] = updated
        return updated
