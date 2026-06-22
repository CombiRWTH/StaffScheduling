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
from scheduling.timeoffice.database import TimeOfficeDatabase, create_db_engine
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.repositories.container import TimeOfficeRepositories
from scheduling.timeoffice.service import TimeOfficeService

settings = get_settings()
configure_logging(level=settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_db_engine(settings=settings)

    facts = TIMEOFFICE_FACTS
    repositories = TimeOfficeRepositories.create(facts=facts)
    database = TimeOfficeDatabase(
        engine=engine,
        repositories=repositories,
        facts=facts,
    )

    app.state.runtime = ApiRuntime(
        timeoffice_service=TimeOfficeService(database=database, facts=facts),
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


@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}
