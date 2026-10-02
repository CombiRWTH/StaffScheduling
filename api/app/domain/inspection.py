"""Read-only planning inspection: the selected month/stations with their complete employee facts."""

from collections.abc import Iterable

from app.domain.availability import Availability
from app.domain.core import NonEmptyStr, SchedulingBaseModel
from app.domain.employee import Employee, EmployeeId, StaffLevel
from app.domain.monthly_work_account import MonthlyWorkAccount
from app.domain.planning_month import PlanningMonth
from app.domain.planning_unit import PlanningUnit, PlanningUnitMembership, PlanningUnitType


class InvalidSelection(ValueError):
    """The request names something that cannot be planned in the month.

    For example an unknown or unplanned station, an employee without a membership, or a non-reference shift.
    """


class EmployeeInspection(SchedulingBaseModel):
    employee_id: EmployeeId
    display_name: NonEmptyStr
    staff_level: StaffLevel
    memberships: tuple[PlanningUnitMembership, ...]
    account: MonthlyWorkAccount
    # Native absences and project availability of the month.
    availability: tuple[Availability, ...]


class PlanningInspection(SchedulingBaseModel):
    planning_month: PlanningMonth
    selected_station_ids: tuple[int, ...]
    # Jumper pools that station members call home; other jumper pool memberships are not an association.
    associated_jumper_pool_ids: tuple[int, ...]
    planning_units: tuple[PlanningUnit, ...]
    employees: tuple[EmployeeInspection, ...]


class PlanningOptions(SchedulingBaseModel):
    planning_month: PlanningMonth
    planning_units: tuple[PlanningUnit, ...]


def inspection_employee_ids(
    *,
    selected_station_ids: tuple[int, ...],
    memberships: Iterable[PlanningUnitMembership],
    jumper_pool_ids: set[int],
) -> set[int]:
    """Select station members plus every member of a jumper pool that one of them calls home.

    A jumper pool is origin context: its members are inspected without implying station eligibility.
    """
    memberships = tuple(memberships)
    associated = _associated_jumper_pool_ids(selected_station_ids, memberships, jumper_pool_ids)
    return {row.employee_id for row in memberships if row.planning_unit_id in {*selected_station_ids, *associated}}


def _associated_jumper_pool_ids(
    selected_station_ids: tuple[int, ...],
    memberships: tuple[PlanningUnitMembership, ...],
    jumper_pool_ids: set[int],
) -> set[int]:
    station_members = {row.employee_id for row in memberships if row.planning_unit_id in selected_station_ids}
    return {
        row.planning_unit_id
        for row in memberships
        if row.employee_id in station_members and row.is_home and row.planning_unit_id in jumper_pool_ids
    }


def build_inspection(
    *,
    planning_month: PlanningMonth,
    selected_station_ids: tuple[int, ...],
    units: tuple[PlanningUnit, ...],
    employees: tuple[Employee, ...],
    memberships: tuple[PlanningUnitMembership, ...],
    accounts: tuple[MonthlyWorkAccount, ...],
    availability: tuple[Availability, ...],
    allowed_shift_ids: set[int],
) -> PlanningInspection:
    """Validate completeness once before exposing any part of an inspection."""
    employee_ids = {employee.employee_id for employee in employees}
    unit_ids = {unit.planning_unit_id for unit in units}
    if len(employee_ids) != len(employees):
        raise ValueError("Duplicate employee identities in inspection.")
    if {row.employee_id for row in memberships} != employee_ids:
        raise ValueError("Employee and membership catalogs are incomplete.")
    account_ids = [row.employee_id for row in accounts]
    if len(set(account_ids)) != len(account_ids) or set(account_ids) != employee_ids:
        raise ValueError("Every employee requires exactly one monthly account.")
    accounts_by_id = {row.employee_id: row for row in accounts}
    for membership in memberships:
        if membership.planning_unit_id not in unit_ids:
            raise ValueError("Unknown membership unit.")
    if any(row.employee_id not in employee_ids for row in availability):
        raise ValueError("Unknown employee in availability.")
    inspected: list[EmployeeInspection] = []
    for employee in employees:
        employee_memberships = tuple(row for row in memberships if row.employee_id == employee.employee_id)
        for day in planning_month.dates:
            active = [row for row in employee_memberships if row.active_on(day)]
            homes = {row.planning_unit_id for row in active if row.is_home}
            if active and len(homes) != 1:
                raise ValueError(f"Employee {employee.employee_id} requires one evidenced home origin on {day}.")
        account = accounts_by_id[employee.employee_id]
        if any(credit.date not in planning_month for credit in account.credit_details):
            raise ValueError("Credit date is outside the selected month.")
        employee_availability = tuple(row for row in availability if row.employee_id == employee.employee_id)
        for row in employee_availability:
            if row.date not in planning_month:
                raise ValueError("Availability date is outside the selected month.")
            if row.shift_ids and not set(row.shift_ids) <= allowed_shift_ids:
                raise ValueError("Unknown allowed shift in availability.")
        inspected.append(
            EmployeeInspection(
                employee_id=employee.employee_id,
                display_name=employee.display_name,
                staff_level=employee.staff_level,
                memberships=employee_memberships,
                account=account,
                availability=employee_availability,
            )
        )
    jumper_pool_ids = {unit.planning_unit_id for unit in units if unit.type == PlanningUnitType.JUMPER_POOL}
    associated = _associated_jumper_pool_ids(selected_station_ids, memberships, jumper_pool_ids)
    return PlanningInspection(
        planning_month=planning_month,
        selected_station_ids=selected_station_ids,
        associated_jumper_pool_ids=tuple(sorted(associated)),
        planning_units=units,
        employees=tuple(inspected),
    )
