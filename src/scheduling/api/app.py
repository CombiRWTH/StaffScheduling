import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query, status

from scheduling.api.dependencies import get_solver_service, get_timeoffice_service
from scheduling.api.types import ApiDate
from scheduling.api.web_router import web_router
from scheduling.logging import configure_logging
from scheduling.models import PlanningPeriod
from scheduling.models.assignment import AssignmentType
from scheduling.models.wish import WishKind
from scheduling.settings import get_settings
from scheduling.solver.tmp import FakeSolution, SolverService
from scheduling.timeoffice.service import TimeOfficeService

settings = get_settings()
configure_logging(level=settings.log_level)

logger = logging.getLogger(__name__)

app = FastAPI(title="Staff Scheduling API")
app.include_router(web_router)

solve_lock = asyncio.Lock()


@app.get("/health")
async def healthcheck():
    return {"status": "healthy"}


@app.get("/debug")
def fetch_timeoffice_dataset(
    station_ids: Annotated[list[int], Query(alias="station")],
    start: Annotated[ApiDate, Query()],
    end: Annotated[ApiDate, Query()],
    timeoffice: Annotated[TimeOfficeService, Depends(get_timeoffice_service)],
) -> dict[str, int]:
    period = PlanningPeriod(start=start, end=end)

    dataset = timeoffice.fetch_dataset(
        planning_unit_ids=tuple(station_ids),
        period=period,
    )

    return {
        "planning_units": len(dataset.planning_units),
        "plans": len(dataset.plans),
        "employees": len(dataset.employees),
        "plan_participants": len(dataset.plan_participants),
        "planning_unit_memberships": len(dataset.planning_unit_memberships),
        "shifts": len(dataset.shifts),
        "assignments": len(dataset.assignments),
        "planned_assignments": sum(
            assignment.assignment_type == AssignmentType.PLANNED for assignment in dataset.assignments
        ),
        "external_assignments": sum(
            assignment.assignment_type == AssignmentType.EXTERNAL for assignment in dataset.assignments
        ),
        "availability": len(dataset.availability),
        "demand_requirements": len(dataset.demand_requirements),
        "sunday_work_history": len(dataset.sunday_work_history),
        "wishes": len(dataset.wishes),
        "shift_wishes": sum(wish.kind == WishKind.SHIFT for wish in dataset.wishes),
        "free_day_wishes": sum(wish.kind == WishKind.FREE_DAY for wish in dataset.wishes),
        "monthly_work_accounts": len(dataset.monthly_work_accounts),
        "employees_without_monthly_work_account": len(dataset.employees) - len(dataset.monthly_work_accounts),
    }


@app.post("/solve")
async def solve_schedule(
    background_tasks: BackgroundTasks,
    solver: Annotated[SolverService, Depends(get_solver_service)],
) -> dict[str, str]:
    try:
        async with asyncio.timeout(2):
            await solve_lock.acquire()
    except TimeoutError as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Solver already working on a different solution. Try again later!",
        ) from e

    unique_id = uuid.uuid4()

    async def task() -> None:
        try:
            await solver.fake_solve(id=unique_id)
        finally:
            solve_lock.release()

    background_tasks.add_task(task)

    return {
        "status": "accepted",
        "solution_id": str(unique_id),
    }


@app.get("/solution")
def get_solution(
    id: Annotated[uuid.UUID, Query()],
    solver: Annotated[SolverService, Depends(get_solver_service)],
) -> FakeSolution:
    solution = next(filter(lambda s: s.id == id, solver.solutions), None)

    if solution is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solution not found!",
        )

    return solution
