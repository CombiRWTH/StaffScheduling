from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from scheduling.domain import (
    EmployeeId,
    Plan,
    PlanId,
    PlanningUnitId,
    PlanningUnitKind,
    SchedulingDataset,
    Shift,
    ShiftId,
)
from scheduling.validation.helpers import ensure_unique


@dataclass(frozen=True, slots=True)
class DatasetValidationContext:
    employee_ids: frozenset[EmployeeId]
    planning_unit_ids: frozenset[PlanningUnitId]
    plan_ids: frozenset[PlanId]
    shift_ids: frozenset[ShiftId]

    plans_by_id: Mapping[PlanId, Plan]
    planning_unit_kind_by_id: Mapping[PlanningUnitId, PlanningUnitKind]
    shifts_by_id: Mapping[ShiftId, Shift]

    @classmethod
    def from_dataset(cls, dataset: SchedulingDataset) -> "DatasetValidationContext":
        employee_ids = ensure_unique(
            (employee.employee_id for employee in dataset.employees),
            "employee_id",
        )
        planning_unit_ids = ensure_unique(
            (unit.planning_unit_id for unit in dataset.planning_units),
            "planning_unit_id",
        )
        plan_ids = ensure_unique(
            (plan.plan_id for plan in dataset.plans),
            "plan_id",
        )
        shift_ids = ensure_unique(
            (shift.shift_id for shift in dataset.shifts),
            "shift_id",
        )

        return cls(
            employee_ids=employee_ids,
            planning_unit_ids=planning_unit_ids,
            plan_ids=plan_ids,
            shift_ids=shift_ids,
            plans_by_id=MappingProxyType({plan.plan_id: plan for plan in dataset.plans}),
            planning_unit_kind_by_id=MappingProxyType(
                {unit.planning_unit_id: unit.kind for unit in dataset.planning_units}
            ),
            shifts_by_id=MappingProxyType({shift.shift_id: shift for shift in dataset.shifts}),
        )
