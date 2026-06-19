from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, Request
from sqlalchemy import Engine

from scheduling.api.solve.job_store import InMemorySolveJobStore
from scheduling.solver.service import SolverService
from scheduling.timeoffice.service import TimeOfficeService


@dataclass(frozen=True, slots=True)
class ApiRuntime:
    engine: Engine
    timeoffice_service: TimeOfficeService
    solver_service: SolverService
    solve_job_store: InMemorySolveJobStore


def get_api_runtime(request: Request) -> ApiRuntime:
    return cast(ApiRuntime, request.app.state.runtime)


def get_timeoffice_service(
    runtime: Annotated[ApiRuntime, Depends(get_api_runtime)],
) -> TimeOfficeService:
    return runtime.timeoffice_service


def get_solver_service(
    runtime: Annotated[ApiRuntime, Depends(get_api_runtime)],
) -> SolverService:
    return runtime.solver_service


def get_solve_job_store(
    runtime: Annotated[ApiRuntime, Depends(get_api_runtime)],
) -> InMemorySolveJobStore:
    return runtime.solve_job_store
