from datetime import timedelta

from app.domain import Availability, Employee, MonthlyWorkAccount, PlanningMonth, PlanningUnit, PlanningUnitMembership
from app.employees.models import EmployeeInspection, EmployeeMonthEvidence, PlanningInspection


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
    return PlanningInspection(
        planning_month=planning_month,
        selected_station_ids=selected_station_ids,
        planning_units=units,
        employees=tuple(inspected),
    )
