import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from scheduling.api.dependencies import ApiRuntime
from scheduling.api.solve.job_store import InMemorySolveJobStore
from scheduling.api.solve.router import solve_router
from scheduling.api.web.router import web_router
from scheduling.logging import configure_logging
from scheduling.settings import get_settings
from scheduling.solver.service import SolverService
from scheduling.timeoffice.database import create_db_engine
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.reading.container import TimeOfficeReaders
from scheduling.timeoffice.service import TimeOfficeService
from scheduling.timeoffice.writing.solution import TimeOfficeSolutionWriter

settings = get_settings()
configure_logging(level=settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_db_engine(settings=settings)
    facts = TIMEOFFICE_FACTS

    app.state.runtime = ApiRuntime(
        timeoffice_service=TimeOfficeService(
            facts=facts,
            engine=engine,
            readers=TimeOfficeReaders.create(facts=facts),
            solution_writer=TimeOfficeSolutionWriter(),
        ),
        solver_service=SolverService(settings=settings),
        solve_job_store=InMemorySolveJobStore(),
        solve_lock=asyncio.Lock(),
    )

    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Staff Scheduling API", lifespan=lifespan)
app.include_router(solve_router)
app.include_router(web_router)


@app.get("/status")
async def healthcheck():
    return {"status": "healthy"}
