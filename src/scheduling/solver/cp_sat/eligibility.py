from datetime import date

from scheduling.domain.availability import AvailabilityType
from scheduling.domain.demand import DemandRequirement
from scheduling.domain.employee import Employee
from scheduling.solver.cp_sat.index import SolverIndex


def is_employee_eligible_for_demand(
    *,
    employee: Employee,
    demand: DemandRequirement,
    index: SolverIndex,
) -> bool:
    return (
        _has_active_membership_for_demand(employee=employee, demand=demand, index=index)
        and not _has_existing_assignment_on_date(employee=employee, demand=demand, index=index)
        and not _is_blocked_by_availability(employee=employee, demand=demand, index=index)
    )


def _has_active_membership_for_demand(
    *,
    employee: Employee,
    demand: DemandRequirement,
    index: SolverIndex,
) -> bool:
    memberships = index.memberships_by_employee_unit.get(
        (employee.employee_id, demand.planning_unit_id),
        [],
    )

    return any(
        membership.staff_level == demand.staff_level
        and _date_in_interval(
            demand.date,
            valid_from=membership.valid_from,
            valid_until=membership.valid_until,
        )
        for membership in memberships
    )


def _date_in_interval(
    target_date: date,
    *,
    valid_from: date,
    valid_until: date | None,
) -> bool:
    return target_date >= valid_from and (valid_until is None or target_date <= valid_until)


def _has_existing_assignment_on_date(
    *,
    employee: Employee,
    demand: DemandRequirement,
    index: SolverIndex,
) -> bool:
    return bool(index.assignments_by_employee_date.get((employee.employee_id, demand.date)))


def _is_blocked_by_availability(
    *,
    employee: Employee,
    demand: DemandRequirement,
    index: SolverIndex,
) -> bool:
    availability_items = index.availability_by_employee_date.get(
        (employee.employee_id, demand.date),
        [],
    )

    hard_blockers = {
        AvailabilityType.UNAVAILABLE,
        AvailabilityType.VACATION,
        AvailabilityType.TRAINING,
        AvailabilityType.FREE_DAY,
    }

    if any(item.availability_type in hard_blockers for item in availability_items):
        return True

    available_only_items = [
        item for item in availability_items if item.availability_type == AvailabilityType.AVAILABLE_ONLY
    ]

    if not available_only_items:
        return False

    allowed_shift_ids = {shift_id for item in available_only_items for shift_id in (item.shift_ids or ())}

    return demand.shift_id not in allowed_shift_ids
