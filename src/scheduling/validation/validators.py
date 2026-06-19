from datetime import date as Date

from scheduling.domain import (
    AssignmentType,
    AvailabilityType,
    EmployeeId,
    PlanId,
    PlanningUnitId,
    PlanningUnitKind,
    ShiftId,
    StaffingDemandRole,
    StaffLevel,
    WishKind,
)
from scheduling.domain.dataset import SchedulingDataset
from scheduling.validation.context import DatasetValidationContext


def validate_plans(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen_planning_units: set[PlanningUnitId] = set()

    for plan in dataset.plans:
        if plan.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(f"Plan references unknown planning_unit_id={plan.planning_unit_id}.")

        if plan.planning_unit_id in seen_planning_units:
            raise ValueError(f"Multiple selected plans reference the same planning_unit_id={plan.planning_unit_id}.")

        seen_planning_units.add(plan.planning_unit_id)


def validate_plan_participants(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen: set[tuple[PlanId, EmployeeId]] = set()

    for participant in dataset.plan_participants:
        if participant.plan_id not in context.plan_ids:
            raise ValueError(f"PlanParticipant references unknown plan_id={participant.plan_id}.")

        if participant.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(f"PlanParticipant references unknown planning_unit_id={participant.planning_unit_id}.")

        if participant.employee_id not in context.employee_ids:
            raise ValueError(f"PlanParticipant references unknown employee_id={participant.employee_id}.")

        plan = context.plans_by_id[participant.plan_id]
        if participant.planning_unit_id != plan.planning_unit_id:
            raise ValueError(
                "PlanParticipant planning_unit_id does not match its Plan: "
                f"plan_id={participant.plan_id} "
                f"participant_planning_unit_id={participant.planning_unit_id} "
                f"plan_planning_unit_id={plan.planning_unit_id}."
            )

        key = (participant.plan_id, participant.employee_id)
        if key in seen:
            raise ValueError(
                f"Duplicate PlanParticipant plan_id={participant.plan_id} employee_id={participant.employee_id}."
            )

        seen.add(key)


def validate_planning_unit_memberships(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen: set[tuple[PlanningUnitId, EmployeeId, Date, Date | None]] = set()

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
    seen: set[tuple[EmployeeId, Date, ShiftId, AssignmentType, PlanningUnitId | None]] = set()

    for assignment in dataset.assignments:
        if not dataset.period.contains(assignment.date):
            raise ValueError(
                f"Assignment outside planning period: employee_id={assignment.employee_id} date={assignment.date}."
            )

        if assignment.employee_id not in context.employee_ids:
            raise ValueError(f"Assignment references unknown employee_id={assignment.employee_id}.")

        if assignment.shift_id not in context.shift_ids:
            raise ValueError(f"Assignment references unknown shift_id={assignment.shift_id}.")

        # Assignment shape invariants belong in Assignment itself.
        # Dataset validation only checks references.
        if (
            assignment.assignment_type == AssignmentType.PLANNED
            and assignment.planning_unit_id is not None
            and assignment.planning_unit_id not in context.planning_unit_ids
        ):
            raise ValueError(f"Planned assignment references unknown planning_unit_id={assignment.planning_unit_id}.")

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
    seen: set[tuple[EmployeeId, Date, AvailabilityType, tuple[ShiftId, ...] | None]] = set()

    for availability in dataset.availability:
        if not dataset.period.contains(availability.date):
            raise ValueError(
                "Availability outside planning period: "
                f"employee_id={availability.employee_id} date={availability.date}."
            )

        if availability.employee_id not in context.employee_ids:
            raise ValueError(f"Availability references unknown employee_id={availability.employee_id}.")

        if availability.shift_ids is not None:
            unknown_shift_ids = sorted(set(availability.shift_ids) - context.shift_ids)
            if unknown_shift_ids:
                raise ValueError(f"Availability references unknown shift_ids={unknown_shift_ids}.")

        key = (
            availability.employee_id,
            availability.date,
            availability.availability_type,
            availability.shift_ids,
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
    seen: set[tuple[PlanningUnitId, Date, ShiftId, StaffLevel]] = set()

    for demand in dataset.demand_requirements:
        if not dataset.period.contains(demand.date):
            raise ValueError(
                "DemandRequirement outside planning period: "
                f"planning_unit_id={demand.planning_unit_id} date={demand.date}."
            )

        if demand.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(f"DemandRequirement references unknown planning_unit_id={demand.planning_unit_id}.")

        if context.planning_unit_kind_by_id[demand.planning_unit_id] != PlanningUnitKind.STATION:
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
    seen: set[tuple[EmployeeId, PlanningUnitId, Date, WishKind, ShiftId | None]] = set()

    for wish in dataset.wishes:
        if wish.employee_id not in context.employee_ids:
            raise ValueError(f"Wish references unknown employee_id={wish.employee_id}.")

        if wish.planning_unit_id not in context.planning_unit_ids:
            raise ValueError(f"Wish references unknown planning_unit_id={wish.planning_unit_id}.")

        if not dataset.period.contains(wish.date):
            raise ValueError(f"Wish date outside planning period: employee_id={wish.employee_id}, date={wish.date}.")

        if wish.shift_id is not None and wish.shift_id not in context.shift_ids:
            raise ValueError(f"Wish references unknown shift_id={wish.shift_id}.")

        key = (
            wish.employee_id,
            wish.planning_unit_id,
            wish.date,
            wish.kind,
            wish.shift_id,
        )

        if key in seen:
            raise ValueError(f"Duplicate wish: {key}.")

        seen.add(key)


def validate_monthly_work_accounts(dataset: SchedulingDataset, context: DatasetValidationContext) -> None:
    seen_employee_ids: set[EmployeeId] = set()

    for account in dataset.monthly_work_accounts:
        if account.employee_id not in context.employee_ids:
            raise ValueError(f"Monthly work account references unknown employee_id={account.employee_id}.")

        if account.employee_id in seen_employee_ids:
            raise ValueError(f"Duplicate monthly work account for employee_id={account.employee_id}.")

        seen_employee_ids.add(account.employee_id)
