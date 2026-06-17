import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Query, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


solver_router = APIRouter()


@dataclass
class FakeSolution:
    id: str
    value: str


solutions: list[FakeSolution] = []
lock = asyncio.Lock()


async def fake_solve(id: uuid.UUID) -> str:
    logger.info("Started processing")
    await asyncio.sleep(5)
    logger.info("Finished processing")

    return f"{id} processed!"


@solver_router.post("/solve")
async def solve_schedule(background_tasks: BackgroundTasks):
    try:
        async with asyncio.timeout(2):
            await lock.acquire()
    except TimeoutError:
        return JSONResponse(
            status_code=status.HTTP_423_LOCKED,
            content={
                "status": "blocked",
                "message": "Solver already working on a different solution. Try again later!",
            },
        )

    unique_id = uuid.uuid4()
    background_tasks.add_task(fake_solve, unique_id)


@solver_router.get("/solution")
def get_solution(id: Annotated[uuid.UUID, Query()]):
    solution = next(filter(lambda s: s.id == id, solutions), None)

    if solution is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "status": "failed",
                "message": "Solution not found!",
            },
        )

    return solution
