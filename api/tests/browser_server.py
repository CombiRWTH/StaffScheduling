"""Offline browser API: production HTTP/read flow with fictional SQL results."""

from time import sleep

import uvicorn
from fastapi import Request
from inspection_fixture import InspectionSource

from app.api.generation import get_generation
from app.api.publication import get_publisher
from app.api.review import get_review
from app.api.shared import get_planning_source
from app.domain import DemandCell, MonthlyDemand, PlanningMonth, SchedulingDataset, StaffLevel
from app.main import app
from app.settings import get_settings
from app.solver.generation import Generation
from app.solver.models import Solution
from app.solver.review import Review
from app.solver.service import SolverService
from app.timeoffice import TimeOfficeService, TimeOfficeUnavailable

source = InspectionSource()


def browser_timeoffice(request: Request) -> TimeOfficeService:
    # Deliberate failure scenarios use months, avoiding test-only application routes.
    if request.query_params.get("month") == "4":
        raise TimeOfficeUnavailable(stage="connection", message="TimeOffice is unavailable; check connection.")
    if request.url.path == "/employees" and request.query_params.get("month") == "6":
        sleep(1)
    source.missing_account = request.query_params.get("month") == "5"
    return source.service


app.dependency_overrides[get_planning_source] = browser_timeoffice

# Station North has saved staffing in June, July and August; September has none, so generation refuses it.
# August asks for two professionals a shift, but only one works at the station, so it is infeasible.
for month in (6, 7, 8):
    planning_month = PlanningMonth(year=2026, month=month)
    cells = tuple(
        DemandCell(
            date=planning_month.start.replace(day=day),
            shift_id=1113,
            staff_level=StaffLevel.PROFESSIONAL,
            required_count=2 if month == 8 else 1,
        )
        for day in (5, 6)
    )
    source.service.save_demand(MonthlyDemand(planning_unit_id=101, planning_month=planning_month, cells=cells))

# Station South needs the jumper-pool MFA in June; without trusted context its schedule is never accepted.
june = PlanningMonth(year=2026, month=6)
source.service.save_demand(
    MonthlyDemand(
        planning_unit_id=102,
        planning_month=june,
        cells=tuple(
            DemandCell(date=june.start.replace(day=day), shift_id=1113, staff_level=StaffLevel.MFA, required_count=1)
            for day in (5, 6)
        ),
    )
)
# Configuration writes for this employee and station fail, so the browser can check failed saves.
source.failing_ids = {3, 102}

solver = SolverService(get_settings())


def browser_input(*, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth) -> SchedulingDataset:
    source.context_plans = 102 not in planning_unit_ids
    return source.service.read_generation_input(planning_unit_ids=planning_unit_ids, planning_month=planning_month)


def browser_solve(dataset: SchedulingDataset, timeout: float) -> Solution:
    """June and August solve for real; July fails at runtime. July and August run visibly long.

    Browser flows request the minimum time limit; the real solves are capped at three seconds.
    """
    month = dataset.planning_month.month
    if month != 6:
        sleep(2)
    if month == 7:
        raise RuntimeError("Fictional solver crash")
    return solver.solve(dataset, timeout=min(timeout, 3))


review = Review(publish=source.service.publish)
generation = Generation(read_input=browser_input, solve=browser_solve, on_solved=review.generated)
app.dependency_overrides[get_generation] = lambda: generation
app.dependency_overrides[get_review] = lambda: review
app.dependency_overrides[get_publisher] = lambda: review

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18080)
