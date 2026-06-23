from collections.abc import Callable

from scheduling.domain import SchedulingDataset
from scheduling.validation.context import DatasetValidationContext
from scheduling.validation.validators import (
    validate_assignments,
    validate_availability,
    validate_demand_requirements,
    validate_monthly_work_accounts,
    validate_planning_unit_memberships,
    validate_plans,
    validate_sunday_work_history,
    validate_wishes,
)

type DatasetValidator = Callable[[SchedulingDataset, DatasetValidationContext], None]


_DATASET_VALIDATORS: tuple[DatasetValidator, ...] = (
    validate_plans,
    validate_planning_unit_memberships,
    validate_assignments,
    validate_availability,
    validate_demand_requirements,
    validate_sunday_work_history,
    validate_wishes,
    validate_monthly_work_accounts,
)


def validate_scheduling_dataset(dataset: SchedulingDataset) -> SchedulingDataset:
    """Validate cross-references and consistency of a canonical scheduling dataset."""
    context = DatasetValidationContext.from_dataset(dataset)

    for validate in _DATASET_VALIDATORS:
        validate(dataset, context)

    return dataset
