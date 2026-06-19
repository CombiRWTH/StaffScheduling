from datetime import date as Date
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from scheduling.domain.core import SchedulingBaseModel
from scheduling.domain.employee import EmployeeId
from scheduling.domain.planning_unit import PlanningUnitId
from scheduling.domain.shift import ShiftId


class WishKind(StrEnum):
    SHIFT = "shift"
    FREE_DAY = "free_day"


class Wish(SchedulingBaseModel):
    employee_id: EmployeeId
    planning_unit_id: PlanningUnitId

    date: Date
    kind: WishKind
    shift_id: ShiftId | None = None

    @model_validator(mode="after")
    def validate_wish(self) -> Self:
        if self.kind == WishKind.SHIFT and self.shift_id is None:
            raise ValueError("SHIFT wish requires shift_id.")

        if self.kind == WishKind.FREE_DAY and self.shift_id is not None:
            raise ValueError("FREE_DAY wish must not define shift_id.")

        return self
