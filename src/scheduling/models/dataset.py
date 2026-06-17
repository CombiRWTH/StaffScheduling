from collections.abc import Sequence
from datetime import date as Date
from typing import Self

from pydantic import model_validator

from src.scheduling.models.assignment import Assignment, AssignmentType
from src.scheduling.models.availability import Availability
from src.scheduling.models.core import SchedulingBaseModel
from src.scheduling.models.demand import DemandRequirement
from src.scheduling.models.employee import Employee, EmployeeId, StaffLevel
from src.scheduling.models.plan import Plan, PlanId, PlanParticipant
from src.scheduling.models.planning_unit import PlanningUnit, PlanningUnitId, PlanningUnitKind, PlanningUnitMembership
from src.scheduling.models.shift import Shift, ShiftId, StaffingDemandRole
from src.scheduling.models.sunday_work_history import EmployeeSundayWorkHistory


class PlanningPeriod(SchedulingBaseModel):
    """Inclusive planning period for one scheduling dataset."""

    start: Date
    end: Date

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        if self.start > self.end:
            raise ValueError(f"PlanningPeriod.start must be before or equal to end: {self.start} > {self.end}")

        return self

    def contains(self, date: Date) -> bool:
        return self.start <= date <= self.end


class SchedulingDataset(SchedulingBaseModel):
    """Clean scheduling dataset aligned with TimeOffice planning concepts.

    This is not solver input yet. Repositories and small transformation functions
    build this reduced model from TimeOffice. Solver-specific indexes and
    OR-Tools variables are derived later.
    """

    period: PlanningPeriod

    planning_units: tuple[PlanningUnit, ...]
    plans: tuple[Plan, ...]

    employees: tuple[Employee, ...] = ()
    plan_participants: tuple[PlanParticipant, ...] = ()
    planning_unit_memberships: tuple[PlanningUnitMembership, ...] = ()

    shifts: tuple[Shift, ...] = ()
    assignments: tuple[Assignment, ...] = ()
    availability: tuple[Availability, ...] = ()

    demand_requirements: tuple[DemandRequirement, ...] = ()

    sunday_work_history: tuple[EmployeeSundayWorkHistory, ...] = ()

    @model_validator(mode="after")
    def validate_dataset(self) -> Self:
        employee_ids = self._unique_employee_ids()
        planning_unit_ids = self._unique_planning_unit_ids()
        plan_ids = self._unique_plan_ids()
        shift_ids = self._unique_shift_ids()

        self._validate_plans(
            planning_unit_ids=planning_unit_ids,
        )
        self._validate_plan_participants(
            employee_ids=employee_ids,
            plan_ids=plan_ids,
            planning_unit_ids=planning_unit_ids,
        )
        self._validate_planning_unit_memberships(
            employee_ids=employee_ids,
            planning_unit_ids=planning_unit_ids,
        )
        self._validate_assignments(
            employee_ids=employee_ids,
            planning_unit_ids=planning_unit_ids,
            shift_ids=shift_ids,
        )
        self._validate_availability(
            employee_ids=employee_ids,
            shift_ids=shift_ids,
        )
        self._validate_demand_requirements(
            planning_unit_ids=planning_unit_ids,
            shift_ids=shift_ids,
        )
        self._validate_sunday_work_history(
            employee_ids=employee_ids,
        )

        return self

    def _unique_employee_ids(self) -> set[EmployeeId]:
        employee_ids = [employee.employee_id for employee in self.employees]
        self._ensure_unique(employee_ids, "employee_id")
        return set(employee_ids)

    def _unique_planning_unit_ids(self) -> set[PlanningUnitId]:
        planning_unit_ids = [unit.planning_unit_id for unit in self.planning_units]
        self._ensure_unique(planning_unit_ids, "planning_unit_id")
        return set(planning_unit_ids)

    def _unique_plan_ids(self) -> set[PlanId]:
        plan_ids = [plan.plan_id for plan in self.plans]
        self._ensure_unique(plan_ids, "plan_id")
        return set(plan_ids)

    def _unique_shift_ids(self) -> set[ShiftId]:
        shift_ids = [shift.shift_id for shift in self.shifts]
        self._ensure_unique(shift_ids, "shift_id")
        return set(shift_ids)

    def _validate_plans(
        self,
        *,
        planning_unit_ids: set[PlanningUnitId],
    ) -> None:
        seen_planning_units: set[PlanningUnitId] = set()

        for plan in self.plans:
            if plan.planning_unit_id not in planning_unit_ids:
                raise ValueError(f"Plan references unknown planning_unit_id={plan.planning_unit_id}.")

            if plan.planning_unit_id in seen_planning_units:
                raise ValueError(
                    f"Multiple selected plans reference the same planning_unit_id={plan.planning_unit_id}."
                )

            seen_planning_units.add(plan.planning_unit_id)

    def _validate_plan_participants(
        self,
        *,
        employee_ids: set[EmployeeId],
        plan_ids: set[PlanId],
        planning_unit_ids: set[PlanningUnitId],
    ) -> None:
        plans_by_id = {plan.plan_id: plan for plan in self.plans}
        seen: set[tuple[PlanId, EmployeeId]] = set()

        for participant in self.plan_participants:
            if participant.plan_id not in plan_ids:
                raise ValueError(f"PlanParticipant references unknown plan_id={participant.plan_id}.")

            if participant.planning_unit_id not in planning_unit_ids:
                raise ValueError(f"PlanParticipant references unknown planning_unit_id={participant.planning_unit_id}.")

            if participant.employee_id not in employee_ids:
                raise ValueError(f"PlanParticipant references unknown employee_id={participant.employee_id}.")

            plan = plans_by_id[participant.plan_id]
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

    def _validate_planning_unit_memberships(
        self,
        *,
        employee_ids: set[EmployeeId],
        planning_unit_ids: set[PlanningUnitId],
    ) -> None:
        seen: set[tuple[PlanningUnitId, EmployeeId, Date, Date | None]] = set()

        for membership in self.planning_unit_memberships:
            if membership.planning_unit_id not in planning_unit_ids:
                raise ValueError(
                    f"PlanningUnitMembership references unknown planning_unit_id={membership.planning_unit_id}."
                )

            if membership.employee_id not in employee_ids:
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

    def _validate_assignments(
        self,
        *,
        employee_ids: set[EmployeeId],
        planning_unit_ids: set[PlanningUnitId],
        shift_ids: set[ShiftId],
    ) -> None:
        seen: set[tuple[EmployeeId, Date, ShiftId, AssignmentType, PlanningUnitId | None]] = set()

        for assignment in self.assignments:
            if not self.period.contains(assignment.date):
                raise ValueError(
                    f"Assignment outside planning period: employee_id={assignment.employee_id} date={assignment.date}."
                )

            if assignment.employee_id not in employee_ids:
                raise ValueError(f"Assignment references unknown employee_id={assignment.employee_id}.")

            if assignment.shift_id not in shift_ids:
                raise ValueError(f"Assignment references unknown shift_id={assignment.shift_id}.")

            if assignment.assignment_type == AssignmentType.PLANNED:
                if assignment.planning_unit_id is None:
                    raise ValueError("Planned assignment must reference planning_unit_id.")

                if assignment.planning_unit_id not in planning_unit_ids:
                    raise ValueError(
                        f"Planned assignment references unknown planning_unit_id={assignment.planning_unit_id}."
                    )

            elif assignment.assignment_type == AssignmentType.EXTERNAL:
                if assignment.planning_unit_id is not None:
                    raise ValueError("External assignment must not reference planning_unit_id.")

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

    def _validate_availability(
        self,
        *,
        employee_ids: set[EmployeeId],
        shift_ids: set[ShiftId],
    ) -> None:
        seen: set[tuple[EmployeeId, Date, str, tuple[ShiftId, ...] | None]] = set()

        for availability in self.availability:
            if not self.period.contains(availability.date):
                raise ValueError(
                    "Availability outside planning period: "
                    f"employee_id={availability.employee_id} date={availability.date}."
                )

            if availability.employee_id not in employee_ids:
                raise ValueError(f"Availability references unknown employee_id={availability.employee_id}.")

            if availability.shift_ids is not None:
                unknown_shift_ids = sorted(set(availability.shift_ids) - shift_ids)
                if unknown_shift_ids:
                    raise ValueError(f"Availability references unknown shift_ids={unknown_shift_ids}.")

            key = (
                availability.employee_id,
                availability.date,
                str(availability.availability_type),
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

    def _validate_demand_requirements(
        self,
        *,
        planning_unit_ids: set[PlanningUnitId],
        shift_ids: set[ShiftId],
    ) -> None:
        planning_unit_kind_by_id = {unit.planning_unit_id: unit.kind for unit in self.planning_units}
        shift_by_id = {shift.shift_id: shift for shift in self.shifts}

        seen: set[tuple[PlanningUnitId, Date, ShiftId, StaffLevel]] = set()

        for demand in self.demand_requirements:
            if not self.period.contains(demand.date):
                raise ValueError(
                    "DemandRequirement outside planning period: "
                    f"planning_unit_id={demand.planning_unit_id} date={demand.date}."
                )

            if demand.planning_unit_id not in planning_unit_ids:
                raise ValueError(f"DemandRequirement references unknown planning_unit_id={demand.planning_unit_id}.")

            if planning_unit_kind_by_id[demand.planning_unit_id] != PlanningUnitKind.STATION:
                raise ValueError(
                    "DemandRequirement must target a station planning unit: "
                    f"planning_unit_id={demand.planning_unit_id}."
                )

            if demand.shift_id not in shift_ids:
                raise ValueError(f"DemandRequirement references unknown shift_id={demand.shift_id}.")

            shift = shift_by_id[demand.shift_id]
            if shift.staffing_role != StaffingDemandRole.REQUIRED_MINIMUM:
                raise ValueError(
                    f"DemandRequirement must reference a REQUIRED_MINIMUM shift: shift_id={demand.shift_id}."
                )

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

    def _validate_sunday_work_history(
        self,
        *,
        employee_ids: set[EmployeeId],
    ) -> None:
        seen: set[EmployeeId] = set()

        for history in self.sunday_work_history:
            if history.employee_id not in employee_ids:
                raise ValueError(f"EmployeeSundayWorkHistory references unknown employee_id={history.employee_id}.")

            if history.employee_id in seen:
                raise ValueError(f"Duplicate EmployeeSundayWorkHistory employee_id={history.employee_id}.")

            seen.add(history.employee_id)

    def _ensure_unique(self, values: Sequence[object], field_name: str) -> None:
        seen: set[object] = set()
        duplicates: set[object] = set()

        for value in values:
            if value in seen:
                duplicates.add(value)

            seen.add(value)

        if duplicates:
            duplicate_values = ", ".join(sorted(str(value) for value in duplicates))
            raise ValueError(f"Duplicate {field_name} values: {duplicate_values}.")
