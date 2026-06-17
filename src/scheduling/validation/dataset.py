from typing import Self

from pydantic import model_validator

from scheduling.models.dataset import SchedulingDataset
from scheduling.validation.context import DatasetValidationContext
from scheduling.validation.validators import (
    validate_assignments,
    validate_availability,
    validate_demand_requirements,
    validate_monthly_work_accounts,
    validate_plan_participants,
    validate_planning_unit_memberships,
    validate_plans,
    validate_sunday_work_history,
    validate_wishes,
)


class ValidatedSchedulingDataset(SchedulingDataset):
    @model_validator(mode="after")
    def validate_cross_references(self) -> Self:
        context = DatasetValidationContext.from_dataset(self)

        validate_plans(self, context)
        validate_plan_participants(self, context)
        validate_planning_unit_memberships(self, context)
        validate_assignments(self, context)
        validate_availability(self, context)
        validate_demand_requirements(self, context)
        validate_sunday_work_history(self, context)
        validate_wishes(self, context)
        validate_monthly_work_accounts(self, context)

        return self
