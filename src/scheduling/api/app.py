import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from scheduling.api.dependencies import ApiRuntime
from scheduling.api.solve.job_store import InMemorySolveJobStore
from scheduling.api.solve.router import solve_router
from scheduling.api.web.employee_router import employee_router
from scheduling.api.web.minimal_staff_router import minimal_staff_router
from scheduling.api.web.weeklyWishes_router import weeklyWishes_router
from scheduling.api.web.wishes_router import wishes_router
from scheduling.logging import configure_logging
from scheduling.settings import get_settings
from scheduling.solver.cp_sat.builder import create_cp_sat_model_builder
from scheduling.solver.service import SolverService
from scheduling.timeoffice.database import create_db_engine
from scheduling.timeoffice.facts import TIMEOFFICE_FACTS
from scheduling.timeoffice.reading.container import TimeOfficeReaders
from scheduling.timeoffice.service import TimeOfficeService
from scheduling.timeoffice.writing.solution import TimeOfficeSolutionWriter
from scheduling.timeoffice.writing.wishes import TimeOfficeWishWriter

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
            wish_writer=TimeOfficeWishWriter(
                target_planning_status_id=facts.target_planning_status_id,
            ),
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
app.include_router(solve_router)
app.include_router(employee_router)
# app.include_router(weights_router)
# app.include_router(availability_router)
app.include_router(wishes_router)
app.include_router(weeklyWishes_router)
app.include_router(minimal_staff_router)


@app.get("/status")
async def healthcheck():
    return {"status": "healthy"}
