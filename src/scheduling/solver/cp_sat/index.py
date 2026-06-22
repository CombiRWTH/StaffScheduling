from collections import defaultdict
from dataclasses import dataclass

from scheduling.domain import (
    Assignment,
    AssignmentType,
    Availability,
    DemandRequirement,
    Employee,
    EmployeeId,
    PlanningUnitId,
    PlanningUnitMembership,
    SchedulingDataset,
    Shift,
    ShiftId,
)
from scheduling.solver.cp_sat.keys import DemandKey, EmployeeDateKey

type MembershipKey = tuple[EmployeeId, PlanningUnitId]


@dataclass(frozen=True, slots=True)
class SolverIndex:
    employees_by_id: dict[EmployeeId, Employee]
    shifts_by_id: dict[ShiftId, Shift]
    memberships_by_employee_unit: dict[MembershipKey, list[PlanningUnitMembership]]
    assignments_by_employee_date: dict[EmployeeDateKey, list[Assignment]]
    availability_by_employee_date: dict[EmployeeDateKey, list[Availability]]
    required_count_by_demand_key: dict[DemandKey, int]
    fixed_planned_count_by_demand_key: dict[DemandKey, int]


def build_schedule_index(dataset: SchedulingDataset) -> SolverIndex:
    employees_by_id = {employee.employee_id: employee for employee in dataset.employees}
    shifts_by_id = {shift.shift_id: shift for shift in dataset.shifts}

    return SolverIndex(
        employees_by_id=employees_by_id,
        shifts_by_id=shifts_by_id,
        memberships_by_employee_unit=_group_memberships(dataset.planning_unit_memberships),
        assignments_by_employee_date=_group_assignments_by_employee_date(dataset.assignments),
        availability_by_employee_date=_group_availability_by_employee_date(dataset.availability),
        required_count_by_demand_key=_count_required_demand_by_key(dataset.demand_requirements),
        fixed_planned_count_by_demand_key=_count_fixed_planned_assignments_by_demand_key(
            assignments=dataset.assignments,
            employees_by_id=employees_by_id,
        ),
    )


def _group_memberships(
    memberships: tuple[PlanningUnitMembership, ...],
) -> dict[MembershipKey, list[PlanningUnitMembership]]:
    grouped: defaultdict[MembershipKey, list[PlanningUnitMembership]] = defaultdict(list)

    for membership in memberships:
        grouped[(membership.employee_id, membership.planning_unit_id)].append(membership)

    return dict(grouped)


def _group_assignments_by_employee_date(
    assignments: tuple[Assignment, ...],
) -> dict[EmployeeDateKey, list[Assignment]]:
    grouped: defaultdict[EmployeeDateKey, list[Assignment]] = defaultdict(list)

    for assignment in assignments:
        grouped[(assignment.employee_id, assignment.date)].append(assignment)

    return dict(grouped)


def _group_availability_by_employee_date(
    availability: tuple[Availability, ...],
) -> dict[EmployeeDateKey, list[Availability]]:
    grouped: defaultdict[EmployeeDateKey, list[Availability]] = defaultdict(list)

    for item in availability:
        grouped[(item.employee_id, item.date)].append(item)

    return dict(grouped)


def _count_required_demand_by_key(
    demand_requirements: tuple[DemandRequirement, ...],
) -> dict[DemandKey, int]:
    required: defaultdict[DemandKey, int] = defaultdict(int)

    for demand in demand_requirements:
        key = (
            demand.planning_unit_id,
            demand.date,
            demand.shift_id,
            demand.staff_level,
        )
        required[key] += demand.required_count

    return dict(required)


def _count_fixed_planned_assignments_by_demand_key(
    *,
    assignments: tuple[Assignment, ...],
    employees_by_id: dict[EmployeeId, Employee],
) -> dict[DemandKey, int]:
    fixed: defaultdict[DemandKey, int] = defaultdict(int)

    for assignment in assignments:
        if assignment.assignment_type != AssignmentType.PLANNED:
            continue

        if assignment.planning_unit_id is None:
            continue

        employee = employees_by_id[assignment.employee_id]
        key = (
            assignment.planning_unit_id,
            assignment.date,
            assignment.shift_id,
            employee.staff_level,
        )
        fixed[key] += 1

    return dict(fixed)
