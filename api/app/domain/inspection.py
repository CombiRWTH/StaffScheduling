"""Read-only planning inspection: the selected month/stations with their complete employee facts."""

from collections.abc import Iterable
from datetime import timedelta

from app.domain.availability import Availability
from app.domain.core import NonEmptyStr, SchedulingBaseModel
from app.domain.employee import Employee, EmployeeId, StaffLevel
from app.domain.monthly_work_account import MonthlyWorkAccount, WorkCredit
from app.domain.planning_month import PlanningMonth
from app.domain.planning_unit import PlanningUnit, PlanningUnitMembership, PlanningUnitType


class InvalidSelection(ValueError):
    """The requested stations cannot be planned for the month (unknown, not a station, or without target)."""


class EmployeeMonthEvidence(SchedulingBaseModel):
    employee_id: EmployeeId
    credit_details: tuple[WorkCredit, ...]
    hard_restrictions: tuple[Availability, ...]
    source: NonEmptyStr


class EmployeeInspection(SchedulingBaseModel):
    employee_id: EmployeeId
    display_name: NonEmptyStr
    staff_level: StaffLevel
    memberships: tuple[PlanningUnitMembership, ...]
    account: MonthlyWorkAccount
    hard_restrictions: tuple[Availability, ...]
    restrictions_source: NonEmptyStr


class PlanningInspection(SchedulingBaseModel):
    planning_month: PlanningMonth
    selected_station_ids: tuple[int, ...]
    # Pools that station members call home; other pool memberships are not an association.
    associated_pool_ids: tuple[int, ...]
    planning_units: tuple[PlanningUnit, ...]
    employees: tuple[EmployeeInspection, ...]


class PlanningOptions(SchedulingBaseModel):
    planning_month: PlanningMonth
    planning_units: tuple[PlanningUnit, ...]


def inspection_employee_ids(
    *,
    selected_station_ids: tuple[int, ...],
    memberships: Iterable[PlanningUnitMembership],
    shared_pool_ids: set[int],
) -> set[int]:
    """Select station members plus every member of a shared pool that one of them calls home.

    A pool is origin context: its members are inspected without implying station eligibility.
    """
    memberships = tuple(memberships)
    pool_ids = _associated_pool_ids(selected_station_ids, memberships, shared_pool_ids)
    return {row.employee_id for row in memberships if row.planning_unit_id in {*selected_station_ids, *pool_ids}}


def _associated_pool_ids(
    selected_station_ids: tuple[int, ...],
    memberships: tuple[PlanningUnitMembership, ...],
    shared_pool_ids: set[int],
) -> set[int]:
    station_members = {row.employee_id for row in memberships if row.planning_unit_id in selected_station_ids}
    return {
        row.planning_unit_id
        for row in memberships
        if row.employee_id in station_members and row.is_home and row.planning_unit_id in shared_pool_ids
    }


def build_inspection(
    *,
    planning_month: PlanningMonth,
    selected_station_ids: tuple[int, ...],
    units: tuple[PlanningUnit, ...],
    employees: tuple[Employee, ...],
    memberships: tuple[PlanningUnitMembership, ...],
    accounts: tuple[MonthlyWorkAccount, ...],
    evidence: tuple[EmployeeMonthEvidence, ...],
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
    for rows in (accounts, evidence):
        row_ids = [row.employee_id for row in rows]
        if len(set(row_ids)) != len(row_ids) or set(row_ids) != employee_ids:
            raise ValueError("Every employee requires exactly one monthly account and evidence declaration.")
    accounts_by_id = {row.employee_id: row for row in accounts}
    evidence_by_id = {row.employee_id: row for row in evidence}
    for membership in memberships:
        if membership.planning_unit_id not in unit_ids:
            raise ValueError("Unknown membership unit.")
    if any(row.employee_id not in employee_ids for row in availability):
        raise ValueError("Unknown employee in restrictions.")
    inspected: list[EmployeeInspection] = []
    for employee in employees:
        employee_memberships = tuple(row for row in memberships if row.employee_id == employee.employee_id)
        for offset in range((planning_month.end - planning_month.start).days + 1):
            day = planning_month.start + timedelta(days=offset)
            active = [
                row
                for row in employee_memberships
                if row.valid_from <= day and (row.valid_until is None or day <= row.valid_until)
            ]
            homes = {row.planning_unit_id for row in active if row.is_home}
            if active and len(homes) != 1:
                raise ValueError(f"Employee {employee.employee_id} requires one evidenced home origin on {day}.")
        declaration = evidence_by_id[employee.employee_id]
        account = MonthlyWorkAccount(
            **accounts_by_id[employee.employee_id].model_dump(
                exclude={"credited_minutes", "credit_details", "evidence_source"}
            ),
            credit_details=declaration.credit_details,
            evidence_source=declaration.source,
        )
        if any(not planning_month.start <= credit.date <= planning_month.end for credit in declaration.credit_details):
            raise ValueError("Credit date is outside the selected month.")
        restrictions = tuple(
            dict.fromkeys(
                (
                    *(row for row in availability if row.employee_id == employee.employee_id),
                    *declaration.hard_restrictions,
                )
            )
        )
        for restriction in restrictions:
            if (
                restriction.employee_id != employee.employee_id
                or not planning_month.start <= restriction.date <= planning_month.end
            ):
                raise ValueError("Restriction identity/date does not match the selected employee month.")
            if restriction.shift_ids and not set(restriction.shift_ids) <= allowed_shift_ids:
                raise ValueError("Unknown allowed shift in hard restriction.")
        inspected.append(
            EmployeeInspection(
                employee_id=employee.employee_id,
                display_name=employee.display_name,
                staff_level=employee.staff_level,
                memberships=employee_memberships,
                account=account,
                hard_restrictions=restrictions,
                restrictions_source=declaration.source,
            )
        )
    pool_ids = {unit.planning_unit_id for unit in units if unit.type == PlanningUnitType.SHARED_POOL}
    return PlanningInspection(
        planning_month=planning_month,
        selected_station_ids=selected_station_ids,
        associated_pool_ids=tuple(sorted(_associated_pool_ids(selected_station_ids, memberships, pool_ids))),
        planning_units=units,
        employees=tuple(inspected),
    )
