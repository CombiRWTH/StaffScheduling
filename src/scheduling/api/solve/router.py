import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from scheduling.api.dependencies import get_solve_job_store, get_solver_service, get_timeoffice_service
from scheduling.api.solve.job_store import InMemorySolveJobStore
from scheduling.api.solve.schemas import SolveAcceptedResponse, SolveCommand, SolveJob, SolveRequest
from scheduling.domain.dataset import PlanningPeriod
from scheduling.solver.service import SolverService
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)


solve_router = APIRouter()
lock = asyncio.Lock()


@solve_router.post("/solve")
async def solve_schedule(
    request: SolveRequest,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
    solver: Annotated[SolverService, Depends(get_solver_service)],
    job_store: Annotated[InMemorySolveJobStore, Depends(get_solve_job_store)],
    background_tasks: BackgroundTasks,
) -> SolveAcceptedResponse:
    command = SolveCommand(
        planning_unit_ids=request.planning_unit_ids,
        period=PlanningPeriod(start=request.start, end=request.end),
    )

    try:
        async with asyncio.timeout(2):
            await lock.acquire()
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Solver already working on a different solution. Try again later!",
        ) from e

    job = job_store.create(command)

    def task(job: SolveJob) -> None:
        try:
            job_store.mark_running(job.job_id)

            dataset = timeoffice.fetch_dataset(
                planning_unit_ids=command.planning_unit_ids,
                period=command.period,
            )

            result = solver.solve(dataset)

            job_store.mark_succeeded(job.job_id, result)
        except Exception as error:
            logger.exception("Solve job failed: job_id=%s", job.job_id)
            job_store.mark_failed(job.job_id, f"{type(error).__name__}: {error}")
        finally:
            lock.release()

    background_tasks.add_task(task, job)

    return SolveAcceptedResponse(
        job_id=job.job_id,
        status=job.status,
    )


@solve_router.get("/solution/{job_id}")
def get_solution(
    job_id: uuid.UUID,
    job_store: Annotated[InMemorySolveJobStore, Depends(get_solve_job_store)],
) -> SolveJob:
    job = job_store.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solve job not found.",
        )

    return job
