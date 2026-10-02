"""The planning selection: stations of a month and the employees they bring."""

from typing import Annotated, Protocol

from fastapi import APIRouter, Depends, Query

from app.api.shared import Month, Year, get_planning_source, planning_errors
from app.domain import EmployeeSummary, PlanningInspection, PlanningMonth, PlanningOptions, PositiveId

router = APIRouter()


class PlanningSource(Protocol):
    def get_planning_options(self, *, planning_month: PlanningMonth) -> PlanningOptions: ...

    def inspect_employees(
        self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth
    ) -> PlanningInspection: ...

    def list_employees(
        self, *, planning_unit_ids: tuple[int, ...], planning_month: PlanningMonth
    ) -> tuple[EmployeeSummary, ...]: ...


Source = Annotated[PlanningSource, Depends(get_planning_source)]
StationIds = Annotated[list[PositiveId], Query(min_length=1)]

INVALID = "Invalid selection: choose configured stations with a target plan for the month."


@router.get("/planning/options")
def get_planning_options(year: Year, month: Month, source: Source) -> PlanningOptions:
    with planning_errors(incomplete="Planning options are incomplete; verify prepared unit/target data."):
        return source.get_planning_options(planning_month=PlanningMonth(year=year, month=month))


@router.get("/employees")
def get_employees(planning_unit_ids: StationIds, year: Year, month: Month, source: Source) -> PlanningInspection:
    with planning_errors(
        invalid=INVALID,
        incomplete="Employee inspection is incomplete. Verify stations, memberships, accounts and monthly evidence.",
    ):
        return source.inspect_employees(
            planning_unit_ids=tuple(planning_unit_ids), planning_month=PlanningMonth(year=year, month=month)
        )


@router.get("/planning/employees")
def get_planning_employees(
    planning_unit_ids: StationIds, year: Year, month: Month, source: Source
) -> tuple[EmployeeSummary, ...]:
    """Who belongs to the selection, without the monthly facts an inspection requires."""
    with planning_errors(invalid=INVALID, incomplete="Employee names or memberships are incomplete."):
        return source.list_employees(
            planning_unit_ids=tuple(planning_unit_ids), planning_month=PlanningMonth(year=year, month=month)
        )
