from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import availability, demand, generation, planning, review
from app.logging import configure_logging
from app.settings import get_settings
from app.solver.bundle import InvalidBundle
from app.solver.generation import Generation
from app.solver.review import Review
from app.solver.service import SolverService
from app.timeoffice import TimeOfficeService, TimeOfficeUnavailable, create_db_engine

settings = get_settings()
configure_logging(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    engine = create_db_engine(settings=settings)
    source = TimeOfficeService(engine)
    solver = SolverService(settings)
    app.state.planning_source = source
    app.state.review = Review()
    app.state.generation = Generation(
        read_input=source.read_generation_input, solve=solver.solve, on_solved=app.state.review.generated
    )
    try:
        yield
    finally:
        app.state.generation.shutdown()
        engine.dispose()


app = FastAPI(title="Staff Scheduling API", lifespan=lifespan)
app.include_router(planning.router)
app.include_router(availability.router)
app.include_router(demand.router)
app.include_router(generation.router)
app.include_router(review.router)


@app.exception_handler(TimeOfficeUnavailable)
async def timeoffice_unavailable(_request: Request, error: TimeOfficeUnavailable) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": str(error), "integration": "timeoffice", "stage": error.stage},
    )


@app.exception_handler(InvalidBundle)
async def invalid_bundle(_request: Request, error: InvalidBundle) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(error), "problem": error.problem})


@app.get("/status")
async def healthcheck():
    return {"status": "healthy"}
