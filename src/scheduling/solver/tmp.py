import asyncio
import logging
import uuid
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FakeSolution:
    id: uuid.UUID
    value: str


class SolverService:
    solutions: list[FakeSolution] = []

    async def fake_solve(self, id: uuid.UUID) -> None:
        logger.info("Started processing")
        await asyncio.sleep(5)
        logger.info("Finished processing")

        solution = FakeSolution(id=id, value=f"{id} processed!")
        self.solutions.append(solution)
