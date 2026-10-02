from app.domain.assignment import Assignment
from app.domain.availability import Availability
from app.domain.core import SchedulingBaseModel
from app.domain.demand import DemandRequirement, MonthlyDemand
from app.domain.employee import Employee
from app.domain.inspection import PlanningInspection
from app.domain.monthly_work_account import MonthlyWorkAccount
from app.domain.plan import Plan
from app.domain.planning_month import PlanningMonth
from app.domain.planning_unit import PlanningUnit, PlanningUnitMembership
from app.domain.shift import Shift
from app.domain.sunday_work_history import EmployeeSundayWorkHistory
from app.domain.wish import Wish


class SchedulingDataset(SchedulingBaseModel):
    """The solver's input for one planning month; solver indexes and OR-Tools variables are derived from it."""

    planning_month: PlanningMonth

    planning_units: tuple[PlanningUnit, ...]
    plans: tuple[Plan, ...]
    shifts: tuple[Shift, ...] = ()
    demand_requirements: tuple[DemandRequirement, ...] = ()

    employees: tuple[Employee, ...] = ()
    planning_unit_memberships: tuple[PlanningUnitMembership, ...] = ()
    sunday_work_history: tuple[EmployeeSundayWorkHistory, ...] = ()
    wishes: tuple[Wish, ...] = ()

    assignments: tuple[Assignment, ...] = ()
    availability: tuple[Availability, ...] = ()

    monthly_work_accounts: tuple[MonthlyWorkAccount, ...] = ()


def build_scheduling_dataset(
    *,
    inspection: PlanningInspection,
    shifts: tuple[Shift, ...],
    demands: tuple[MonthlyDemand | None, ...],
) -> SchedulingDataset:
    """The full-month generation input of a validated inspection; every selected station needs saved demand.

    The selected stations are the only assignable units; associated jumper pools stay origin context.
    Wishes, existing assignments and plans are deliberately left out: generation does not consider wishes yet,
    no trusted fixed or boundary assignments exist, and plans are write-back context.
    """
    selected = inspection.selected_station_ids
    saved = {demand.planning_unit_id: demand for demand in demands if demand is not None}
    if missing := [station_id for station_id in selected if station_id not in saved]:
        raise ValueError(f"No saved staffing demand for planning_unit_ids={missing}.")
    unit_ids = {*selected, *inspection.associated_jumper_pool_ids}
    return SchedulingDataset(
        planning_month=inspection.planning_month,
        planning_units=tuple(unit for unit in inspection.planning_units if unit.planning_unit_id in unit_ids),
        plans=(),
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
    )
