import asyncio
from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, Request

from scheduling.api.solve.job_store import InMemorySolveJobStore
from scheduling.solver.service import SolverService
from scheduling.timeoffice.service import TimeOfficeService


@dataclass(frozen=True, slots=True)
class ApiRuntime:
    timeoffice_service: TimeOfficeService
    solver_service: SolverService
    solve_job_store: InMemorySolveJobStore
    solve_lock: asyncio.Lock


def get_api_runtime(request: Request) -> ApiRuntime:
    runtime = getattr(request.app.state, "runtime", None)

    if runtime is None:
        raise RuntimeError("API runtime has not been initialized.")

    return cast(ApiRuntime, runtime)


def get_timeoffice_service(runtime: Annotated[ApiRuntime, Depends(get_api_runtime)]) -> TimeOfficeService:
    return runtime.timeoffice_service


def get_solver_service(runtime: Annotated[ApiRuntime, Depends(get_api_runtime)]) -> SolverService:
    return runtime.solver_service


def get_solve_lock(runtime: Annotated[ApiRuntime, Depends(get_api_runtime)]) -> asyncio.Lock:
    return runtime.solve_lock


def get_solve_job_store(runtime: Annotated[ApiRuntime, Depends(get_api_runtime)]) -> InMemorySolveJobStore:
    return runtime.solve_job_store
