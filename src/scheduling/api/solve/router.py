import asyncio
import logging
import uuid
from time import monotonic
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from scheduling.api.dependencies import get_solve_job_store, get_solve_lock, get_solver_service, get_timeoffice_service
from scheduling.api.solve.job_models import SolveCommand, SolveJob
from scheduling.api.solve.job_store import InMemorySolveJobStore
from scheduling.api.solve.schemas import SolveAcceptedResponse, SolveOptions, SolveRequest
from scheduling.solver.models import Solution
from scheduling.solver.service import SolverService
from scheduling.timeoffice.service import TimeOfficeService

logger = logging.getLogger(__name__)

solve_router = APIRouter(prefix="/solve")


@solve_router.get("/options")
def get_solve_options(
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> SolveOptions:
    return timeoffice.get_solve_options()


@solve_router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def create_solve_task(
    request: SolveRequest,
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
    solver: Annotated[SolverService, Depends(get_solver_service)],
    job_store: Annotated[InMemorySolveJobStore, Depends(get_solve_job_store)],
    solve_lock: Annotated[asyncio.Lock, Depends(get_solve_lock)],
    background_tasks: BackgroundTasks,
) -> SolveAcceptedResponse:
    command = SolveCommand(
        planning_unit_ids=request.planning_unit_ids,
        planning_month=request.planning_month(),
    )

    if solve_lock.locked():
        logger.info(
            "Solve job rejected because solver is busy: planning_units=%s planning_month=%s",
            command.planning_unit_ids,
            command.planning_month.label,
        )
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Solver is already working on another solution. Try again later.",
        )

    await solve_lock.acquire()

    job = job_store.create(command)
    logger.info(
        "Solve job accepted: job_id=%s planning_units=%s planning_month=%s",
        job.job_id,
        command.planning_unit_ids,
        command.planning_month.label,
    )

    def kernel(command: SolveCommand) -> Solution:
        logger.info(
            "Fetching scheduling dataset for solve job: job_id=%s planning_units=%s planning_month=%s",
            job.job_id,
            command.planning_unit_ids,
            command.planning_month.label,
        )

        dataset = timeoffice.fetch_dataset(
            planning_unit_ids=command.planning_unit_ids,
            planning_month=command.planning_month,
        )

        logger.info("Solving scheduling dataset for solve job: job_id=%s", job.job_id)
        solution = solver.solve(dataset)

        logger.info("Running TimeOffice writeback dry-run for solve job: job_id=%s", job.job_id)
        timeoffice.write_solution_dry_run(solution)

        return solution

    async def task() -> None:
        """Run the accepted solve job and persist its lifecycle state."""
        started = monotonic()

        try:
            job_store.mark_running(job.job_id)
            logger.info("Solve job started: job_id=%s", job.job_id)

            result = await asyncio.to_thread(kernel, command)

            job_store.mark_succeeded(job.job_id, result)
            logger.info(
                "Solve job succeeded: job_id=%s duration_seconds=%.2f",
                job.job_id,
                monotonic() - started,
            )

        except Exception as e:
            logger.exception(
                "Solve job failed: job_id=%s duration_seconds=%.2f",
                job.job_id,
                monotonic() - started,
            )
            try:
                job_store.mark_failed(job.job_id, f"{type(e).__name__}: {e}")
            except Exception:
                logger.exception("Failed to mark solve job as failed: job_id=%s", job.job_id)

        finally:
            solve_lock.release()

    background_tasks.add_task(task)

    return SolveAcceptedResponse(
        job_id=job.job_id,
        status=job.status,
    )


@solve_router.get("/jobs/{job_id}")
async def check_solve_task(
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
