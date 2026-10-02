from datetime import timedelta
from typing import Self

from pydantic import model_validator

from app.domain.availability import Availability
from app.domain.calendar import dates_between
from app.domain.context import ScheduleContext
from app.domain.core import SchedulingBaseModel
from app.domain.demand import DemandRequirement, MonthlyDemand
from app.domain.duty import duty_times
from app.domain.employee import Employee
from app.domain.inspection import PlanningInspection
from app.domain.monthly_work_account import MonthlyWorkAccount
from app.domain.planning_month import PlanningMonth
from app.domain.planning_unit import PlanningUnit, PlanningUnitMembership, PlanningUnitType
from app.domain.shift import Shift


class SchedulingDataset(SchedulingBaseModel):
    """The complete input of one full-month run for the selected stations.

    The station units are the only destinations; jumper pools are origin context. Every employee
    has exactly one account; `context` carries the trusted duties around the month. Solver and
    schedule check read the same dataset, so it validates all references once.
    """

    planning_month: PlanningMonth
    planning_units: tuple[PlanningUnit, ...]
    shifts: tuple[Shift, ...]
    demand_requirements: tuple[DemandRequirement, ...]
    employees: tuple[Employee, ...]
    planning_unit_memberships: tuple[PlanningUnitMembership, ...]
    availability: tuple[Availability, ...]
    monthly_work_accounts: tuple[MonthlyWorkAccount, ...]
    context: ScheduleContext

    @model_validator(mode="after")
    def validate_references(self) -> Self:
        month = self.planning_month
        employee_ids = [row.employee_id for row in self.employees]
        shift_ids = {row.shift_id for row in self.shifts}
        stations = {row.planning_unit_id for row in self.planning_units if row.type == PlanningUnitType.STATION}
        if len(set(employee_ids)) != len(employee_ids) or len(shift_ids) != len(self.shifts):
            raise ValueError("Duplicate employee or shift identities.")
        if sorted(row.employee_id for row in self.monthly_work_accounts) != sorted(employee_ids):
            raise ValueError("Every employee requires exactly one monthly account.")
        if any(row.employee_id not in employee_ids for row in self.planning_unit_memberships):
            raise ValueError("Membership of an unknown employee.")
        demand_keys = [(r.planning_unit_id, r.date, r.shift_id, r.staff_level) for r in self.demand_requirements]
        if len(set(demand_keys)) != len(demand_keys):
            raise ValueError("Duplicate demand requirement.")
        for row in self.demand_requirements:
            if row.planning_unit_id not in stations or row.shift_id not in shift_ids:
                raise ValueError("Demand for an unknown station or shift.")
            if not month.start <= row.date <= month.end:
                raise ValueError("Demand date is outside the planning month.")
        for row in self.availability:
            if row.employee_id not in employee_ids or not month.start <= row.date <= month.end:
                raise ValueError("Availability of an unknown employee or outside the planning month.")
        self._validate_context(set(employee_ids), shift_ids)
        # Every possible duty must have unambiguous local times, so the run cannot fail on them later.
        for day in dates_between(month.start, month.end):
            for shift in self.shifts:
                duty_times(day, shift)
        return self

    def _validate_context(self, employee_ids: set[int], shift_ids: set[int]) -> None:
        month, context = self.planning_month, self.context
        if not context.covered_from <= month.start or not month.end <= context.covered_until:
            raise ValueError("Context coverage must include the planning month.")
        keys = [(row.employee_id, row.date) for row in context.duties]
        if len(set(keys)) != len(keys):
            raise ValueError("Context has more than one duty for one employee and date.")
        for row in context.duties:
            if row.employee_id not in employee_ids or row.shift_id not in shift_ids:
                raise ValueError("Context duty of an unknown employee or shift.")
            if month.start <= row.date <= month.end or not context.covered_from <= row.date <= context.covered_until:
                raise ValueError("Context duties lie inside their coverage and outside the planning month.")
            duty_times(row.date, next(shift for shift in self.shifts if shift.shift_id == row.shift_id))
        after = month.end + timedelta(days=1)
        if any(row.employee_id not in employee_ids or row.date != after for row in context.availability):
            raise ValueError("Context availability belongs to a known employee and the date after the month.")


def build_scheduling_dataset(
    *,
    inspection: PlanningInspection,
    shifts: tuple[Shift, ...],
    demands: tuple[MonthlyDemand | None, ...],
    context: ScheduleContext,
) -> SchedulingDataset:
    """The full-month generation input of a validated inspection; every selected station needs saved demand.

    The selected stations are the only assignable units; associated jumper pools stay origin context.
    Wishes are not an input: the agreed examples contain no soft employee preferences.
    """
    selected = inspection.selected_station_ids
    saved = {demand.planning_unit_id: demand for demand in demands if demand is not None}
    if missing := [station_id for station_id in selected if station_id not in saved]:
        raise ValueError(f"No saved staffing demand for planning_unit_ids={missing}.")
    unit_ids = {*selected, *inspection.associated_jumper_pool_ids}
    return SchedulingDataset(
        planning_month=inspection.planning_month,
        planning_units=tuple(unit for unit in inspection.planning_units if unit.planning_unit_id in unit_ids),
        shifts=shifts,
        demand_requirements=tuple(row for station_id in selected for row in saved[station_id].requirements),
        employees=tuple(
            Employee(employee_id=row.employee_id, display_name=row.display_name, staff_level=row.staff_level)
            for row in inspection.employees
        ),
        planning_unit_memberships=tuple(
            membership
            for row in inspection.employees
            for membership in row.memberships
            if membership.planning_unit_id in unit_ids
        ),
        availability=tuple(entry for row in inspection.employees for entry in row.availability),
        monthly_work_accounts=tuple(row.account for row in inspection.employees),
        context=context,
    )
