import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Query

from scheduling.api.dependencies import ApiRuntime, get_timeoffice_service
from scheduling.api.solve.job_store import InMemorySolveJobStore
from scheduling.api.solve.router import solve_router
from scheduling.api.types import ApiDate
from scheduling.api.web.router import web_router
from scheduling.domain import PlanningPeriod
from scheduling.domain.assignment import AssignmentType
from scheduling.domain.wish import WishKind
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
    configure_logging(level=settings.log_level)

    engine = create_db_engine(settings=settings)
    facts = TIMEOFFICE_FACTS
    repositories = TimeOfficeRepositories.create(facts=facts)
    database = TimeOfficeDatabase(
        engine=engine,
        repositories=repositories,
        facts=facts,
    )

    app.state.runtime = ApiRuntime(
        engine=engine,
        timeoffice_service=TimeOfficeService(database=database, facts=facts),
        solver_service=SolverService(),
        solve_job_store=InMemorySolveJobStore(),
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
