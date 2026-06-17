import logging

from fastapi import FastAPI

from src.scheduling.api.data_router import data_router
from src.scheduling.api.solver_router import solver_router
from src.scheduling.logging import configure_logging
from src.scheduling.settings import get_settings

settings = get_settings()
configure_logging(level=settings.log_level)

logger = logging.getLogger(__name__)

app = FastAPI(title="Staff Scheduling API")
app.include_router(solver_router, prefix="/solver")
app.include_router(data_router, prefix="/data")


@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}
