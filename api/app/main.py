from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.planning import router as planning_router
from app.logging import configure_logging
from app.settings import get_settings
from app.timeoffice import TimeOfficeService, TimeOfficeUnavailable, create_db_engine

settings = get_settings()
configure_logging(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    engine = create_db_engine(settings=settings)
    app.state.planning_source = TimeOfficeService(engine)
    try:
        yield
    finally:
        engine.dispose()


app = FastAPI(title="Staff Scheduling API", lifespan=lifespan)
app.include_router(planning_router)


@app.exception_handler(TimeOfficeUnavailable)
async def timeoffice_unavailable(_request: Request, error: TimeOfficeUnavailable) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={"detail": str(error), "integration": "timeoffice", "stage": error.stage},
    )


@app.get("/status")
async def healthcheck():
    return {"status": "healthy"}
