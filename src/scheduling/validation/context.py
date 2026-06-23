from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType

from scheduling.domain import EmployeeId, PlanId, PlanningUnitId, PlanningUnitType, SchedulingDataset, Shift, ShiftId


@dataclass(frozen=True, slots=True)
class DatasetValidationContext:
    employee_ids: frozenset[EmployeeId]
    planning_unit_ids: frozenset[PlanningUnitId]
    plan_ids: frozenset[PlanId]
    shift_ids: frozenset[ShiftId]

    planning_unit_type_by_id: Mapping[PlanningUnitId, PlanningUnitType]
    shifts_by_id: Mapping[ShiftId, Shift]

    @classmethod
    def from_dataset(cls, dataset: SchedulingDataset) -> "DatasetValidationContext":
        employee_ids = _ensure_unique(
            (employee.employee_id for employee in dataset.employees),
            "employee_id",
        )
        planning_unit_ids = _ensure_unique(
            (unit.planning_unit_id for unit in dataset.planning_units),
            "planning_unit_id",
        )
        plan_ids = _ensure_unique(
            (plan.plan_id for plan in dataset.plans),
            "plan_id",
        )
        shift_ids = _ensure_unique(
            (shift.shift_id for shift in dataset.shifts),
            "shift_id",
        )

        return cls(
            employee_ids=employee_ids,
            planning_unit_ids=planning_unit_ids,
            plan_ids=plan_ids,
            shift_ids=shift_ids,
            planning_unit_type_by_id=MappingProxyType(
                {unit.planning_unit_id: unit.type for unit in dataset.planning_units}
            ),
            shifts_by_id=MappingProxyType({shift.shift_id: shift for shift in dataset.shifts}),
        )


def _ensure_unique[T](values: Iterable[T], field_name: str) -> frozenset[T]:
    seen: set[T] = set()
    duplicates: set[T] = set()

    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)

    if duplicates:
        duplicate_values = ", ".join(sorted(str(value) for value in duplicates))
        raise ValueError(f"Duplicate {field_name} values: {duplicate_values}.")

    return frozenset(seen)
