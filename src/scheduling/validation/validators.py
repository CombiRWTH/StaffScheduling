from datetime import date

from scheduling.domain import (
    AssignmentType,
    AvailabilityType,
    EmployeeId,
    PlanningMonth,
    PlanningUnitId,
    PlanningUnitType,
    SchedulingDataset,
    ShiftId,
    StaffingDemandRole,
    StaffLevel,
    WishType,
)
from scheduling.validation.context import DatasetValidationContext


def validate_plans(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen_planning_units: set[PlanningUnitId] = set()

    for plan in dataset.plans:
        if plan.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(f"Plan references unknown planning_unit_id={plan.planning_unit_id}.")

        if plan.planning_unit_id in seen_planning_units:
            raise ValueError(f"Multiple selected plans reference the same planning_unit_id={plan.planning_unit_id}.")

        seen_planning_units.add(plan.planning_unit_id)


def validate_planning_unit_memberships(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen: set[tuple[PlanningUnitId, EmployeeId, date, date | None]] = set()

    for membership in dataset.planning_unit_memberships:
        if membership.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(
                f"PlanningUnitMembership references unknown planning_unit_id={membership.planning_unit_id}."
            )

        if membership.employee_id not in context.employee_ids:
            raise ValueError(f"PlanningUnitMembership references unknown employee_id={membership.employee_id}.")

        key = (
            membership.planning_unit_id,
            membership.employee_id,
            membership.valid_from,
            membership.valid_until,
        )
        if key in seen:
            raise ValueError(
                "Duplicate PlanningUnitMembership "
                f"planning_unit_id={membership.planning_unit_id} "
                f"employee_id={membership.employee_id} "
                f"valid_from={membership.valid_from} "
                f"valid_until={membership.valid_until}."
            )

        seen.add(key)


def validate_assignments(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen: set[tuple[EmployeeId, date, ShiftId, AssignmentType, PlanningUnitId | None]] = set()

    for assignment in dataset.assignments:
        if assignment.assignment_type == AssignmentType.GENERATED:
            raise ValueError(
                "SchedulingDataset must not contain generated assignments. "
                "Generated assignments belong to Solution, not imported dataset facts."
            )

        _validate_date_in_planning_month(
            planning_month=dataset.planning_month,
            value=assignment.date,
            label="Assignment",
            details=f"employee_id={assignment.employee_id}",
        )

        if assignment.employee_id not in context.employee_ids:
            raise ValueError(f"Assignment references unknown employee_id={assignment.employee_id}.")

        if assignment.shift_id not in context.shift_ids:
            raise ValueError(f"Assignment references unknown shift_id={assignment.shift_id}.")

        if assignment.planning_unit_id is not None and assignment.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(f"Assignment references unknown planning_unit_id={assignment.planning_unit_id}.")

        key = (
            assignment.employee_id,
            assignment.date,
            assignment.shift_id,
            assignment.assignment_type,
            assignment.planning_unit_id,
        )
        if key in seen:
            raise ValueError(
                f"Duplicate assignment employee_id={assignment.employee_id} "
                f"date={assignment.date} shift_id={assignment.shift_id} "
                f"type={assignment.assignment_type} "
                f"planning_unit_id={assignment.planning_unit_id}."
            )

        seen.add(key)


def validate_availability(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen: set[tuple[EmployeeId, date, AvailabilityType, tuple[ShiftId, ...] | None]] = set()

    for availability in dataset.availability:
        _validate_date_in_planning_month(
            planning_month=dataset.planning_month,
            value=availability.date,
            label="Availability",
            details=f"employee_id={availability.employee_id}",
        )

        if availability.employee_id not in context.employee_ids:
            raise ValueError(f"Availability references unknown employee_id={availability.employee_id}.")

        normalized_shift_ids = None
        if availability.shift_ids is not None:
            normalized_shift_ids = tuple(sorted(availability.shift_ids))
            unknown_shift_ids = sorted(set(normalized_shift_ids) - context.shift_ids)
            if unknown_shift_ids:
                raise ValueError(f"Availability references unknown shift_ids={unknown_shift_ids}.")

        key = (
            availability.employee_id,
            availability.date,
            availability.availability_type,
            normalized_shift_ids,
        )
        if key in seen:
            raise ValueError(
                f"Duplicate availability employee_id={availability.employee_id} "
                f"date={availability.date} "
                f"type={availability.availability_type} "
                f"shift_ids={availability.shift_ids}."
            )

        seen.add(key)


def validate_demand_requirements(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen: set[tuple[PlanningUnitId, date, ShiftId, StaffLevel]] = set()

    for demand in dataset.demand_requirements:
        _validate_date_in_planning_month(
            planning_month=dataset.planning_month,
            value=demand.date,
            label="DemandRequirement",
            details=f"planning_unit_id={demand.planning_unit_id}",
        )

        if demand.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(f"DemandRequirement references unknown planning_unit_id={demand.planning_unit_id}.")

        if context.planning_unit_type_by_id[demand.planning_unit_id] != PlanningUnitType.STATION:
            raise ValueError(
                f"DemandRequirement must target a station planning unit: planning_unit_id={demand.planning_unit_id}."
            )

        if demand.shift_id not in context.shift_ids:
            raise ValueError(f"DemandRequirement references unknown shift_id={demand.shift_id}.")

        shift = context.shifts_by_id[demand.shift_id]
        if shift.staffing_role != StaffingDemandRole.REQUIRED_MINIMUM:
            raise ValueError(f"DemandRequirement must reference a REQUIRED_MINIMUM shift: shift_id={demand.shift_id}.")

        key = (
            demand.planning_unit_id,
            demand.date,
            demand.shift_id,
            demand.staff_level,
        )
        if key in seen:
            raise ValueError(
                "Duplicate DemandRequirement "
                f"planning_unit_id={demand.planning_unit_id} "
                f"date={demand.date} "
                f"shift_id={demand.shift_id} "
                f"staff_level={demand.staff_level}."
            )

        seen.add(key)


def validate_sunday_work_history(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen: set[EmployeeId] = set()

    for history in dataset.sunday_work_history:
        if history.employee_id not in context.employee_ids:
            raise ValueError(f"EmployeeSundayWorkHistory references unknown employee_id={history.employee_id}.")

        if history.employee_id in seen:
            raise ValueError(f"Duplicate EmployeeSundayWorkHistory employee_id={history.employee_id}.")

        seen.add(history.employee_id)


def validate_wishes(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen: set[tuple[EmployeeId, PlanningUnitId, date, WishType, ShiftId | None]] = set()

    for wish in dataset.wishes:
        if wish.employee_id not in context.employee_ids:
            raise ValueError(f"Wish references unknown employee_id={wish.employee_id}.")

        if wish.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(f"Wish references unknown planning_unit_id={wish.planning_unit_id}.")

        _validate_date_in_planning_month(
            planning_month=dataset.planning_month,
            value=wish.date,
            label="Wish",
            details=f"employee_id={wish.employee_id}",
        )

        if wish.shift_id is not None and wish.shift_id not in context.shift_ids:
            raise ValueError(f"Wish references unknown shift_id={wish.shift_id}.")

        key = (
            wish.employee_id,
            wish.planning_unit_id,
            wish.date,
            wish.type,
            wish.shift_id,
        )
        if key in seen:
            raise ValueError(
                "Duplicate Wish "
                f"employee_id={wish.employee_id} "
                f"planning_unit_id={wish.planning_unit_id} "
                f"date={wish.date} "
                f"type={wish.type} "
                f"shift_id={wish.shift_id}."
            )

        seen.add(key)


def validate_monthly_work_accounts(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen_employee_ids: set[EmployeeId] = set()

    for account in dataset.monthly_work_accounts:
        if account.employee_id not in context.employee_ids:
            raise ValueError(f"MonthlyWorkAccount references unknown employee_id={account.employee_id}.")

        if account.employee_id in seen_employee_ids:
            raise ValueError(f"Duplicate MonthlyWorkAccount employee_id={account.employee_id}.")

        seen_employee_ids.add(account.employee_id)


def _validate_date_in_planning_month(
    *,
    planning_month: PlanningMonth,
    value: date,
    label: str,
    details: str,
) -> None:
    if planning_month.start <= value <= planning_month.end:
        return

    raise ValueError(f"{label} outside planning month: {details} date={value} planning_month={planning_month.label}.")
