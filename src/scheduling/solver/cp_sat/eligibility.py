from datetime import date

from scheduling.domain.availability import AvailabilityType
from scheduling.domain.employee import Employee, StaffLevel
from scheduling.domain.planning_unit import PlanningUnitId
from scheduling.domain.shift import ShiftId
from scheduling.solver.index import SolverIndex


def eligible_staff_levels_for_assignment_slot(
    *,
    employee: Employee,
    planning_unit_id: PlanningUnitId,
    assignment_date: date,
    shift_id: ShiftId,
    index: SolverIndex,
) -> tuple[StaffLevel, ...]:
    """Return staff levels under which an employee may work one generated slot.

    Temporary migration behavior:
    imported TimeOffice assignments are intentionally ignored by the solver for now.
    They do not block generated assignments and do not count as fixed coverage.

    Current hard eligibility rules:
    - employee must have an active membership in the planning unit
    - employee must not be blocked by hard availability
    - AVAILABLE_ONLY restrictions must include the target shift

    Future hard rules belong here too:
    - shared/jump-pool eligibility
    - qualifications
    - legal hard constraints that can safely pre-filter slots
    """
    if _is_blocked_by_availability(
        employee=employee,
        assignment_date=assignment_date,
        shift_id=shift_id,
        index=index,
    ):
        return ()

    return _active_membership_staff_levels(
        employee=employee,
        planning_unit_id=planning_unit_id,
        assignment_date=assignment_date,
        index=index,
    )


def _active_membership_staff_levels(
    *,
    employee: Employee,
    planning_unit_id: PlanningUnitId,
    assignment_date: date,
    index: SolverIndex,
) -> tuple[StaffLevel, ...]:
    memberships = index.memberships_by_employee_unit.get(
        (employee.employee_id, planning_unit_id),
        [],
    )

    staff_levels = {
        membership.staff_level
        for membership in memberships
        if _date_in_interval(
            assignment_date,
            valid_from=membership.valid_from,
            valid_until=membership.valid_until,
        )
    }

    return tuple(sorted(staff_levels, key=lambda staff_level: staff_level.value))


def _date_in_interval(
    target_date: date,
    *,
    valid_from: date,
    valid_until: date | None,
) -> bool:
    return target_date >= valid_from and (valid_until is None or target_date <= valid_until)


def _is_blocked_by_availability(
    *,
    employee: Employee,
    assignment_date: date,
    shift_id: ShiftId,
    index: SolverIndex,
) -> bool:
    availability_items = index.availability_by_employee_date.get(
        (employee.employee_id, assignment_date),
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

    allowed_shift_ids = {
        allowed_shift_id for item in available_only_items for allowed_shift_id in (item.shift_ids or ())
    }

    return shift_id not in allowed_shift_ids
