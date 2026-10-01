import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.dependencies import ApiRuntime
from app.employees.router import router as employees_router
from app.logging import configure_logging
from app.routers.solve.job_store import InMemorySolveJobStore
from app.routers.solve.router import solve_router
from app.settings import get_settings
from app.solver.cp_sat.builder import create_cp_sat_model_builder
from app.solver.service import SolverService
from app.timeoffice.database import TimeOfficeUnavailable, create_db_engine
from app.timeoffice.facts import TIMEOFFICE_FACTS
from app.timeoffice.reading.container import TimeOfficeReaders
from app.timeoffice.service import TimeOfficeService
from app.timeoffice.writing.solution import TimeOfficeSolutionWriter

settings = get_settings()
configure_logging(level=settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    engine = create_db_engine(settings=settings)
    facts = TIMEOFFICE_FACTS

    model_builder = create_cp_sat_model_builder()

    app.state.runtime = ApiRuntime(
        timeoffice_service=TimeOfficeService(
            facts=facts,
            engine=engine,
            readers=TimeOfficeReaders.create(facts=facts),
            solution_writer=TimeOfficeSolutionWriter(),
        ),
        solver_service=SolverService(
            settings=settings,
            model_builder=model_builder,
        ),
        solve_job_store=InMemorySolveJobStore(),
        solve_lock=asyncio.Lock(),
    )

    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Staff Scheduling API", lifespan=lifespan)
app.include_router(employees_router)
app.include_router(solve_router)


@app.exception_handler(TimeOfficeUnavailable)
async def timeoffice_unavailable(_request: Request, error: TimeOfficeUnavailable) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": str(error), "integration": "timeoffice", "stage": error.stage},
    )


@app.get("/status")
async def healthcheck():
    return {"status": "healthy"}
