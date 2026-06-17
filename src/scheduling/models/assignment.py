from datetime import date as Date
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from scheduling.models.core import SchedulingBaseModel
from scheduling.models.employee import EmployeeId
from scheduling.models.planning_unit import PlanningUnitId
from scheduling.models.shift import ShiftId


class AssignmentType(StrEnum):
    """Type of existing TimeOffice assignment in the imported dataset."""

    PLANNED = "planned"
    EXTERNAL = "external"


class Assignment(SchedulingBaseModel):
    """Imported existing TimeOffice work assignment.

    PLANNED assignments belong to one of the selected planning units.

    EXTERNAL assignments are work assignments of selected employees outside the
    selected scheduling context. They block the employee via the referenced
    shift, but they do not satisfy selected planning-unit demand.
    """

    employee_id: EmployeeId
    date: Date
    shift_id: ShiftId

    assignment_type: AssignmentType

    # Required for PLANNED assignments. External work only blocks the employee,
    # so its original TimeOffice planning unit is intentionally not exposed.
    planning_unit_id: PlanningUnitId | None = None

    @model_validator(mode="after")
    def validate_assignment(self) -> Self:
        if self.assignment_type == AssignmentType.PLANNED and self.planning_unit_id is None:
            raise ValueError("Planned assignment must reference planning_unit_id.")

        if self.assignment_type == AssignmentType.EXTERNAL and self.planning_unit_id is not None:
            raise ValueError("External assignment must not reference planning_unit_id.")

        return self
