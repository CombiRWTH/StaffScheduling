from datetime import date as Date
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from scheduling.domain.core import SchedulingBaseModel
from scheduling.domain.employee import EmployeeId
from scheduling.domain.planning_month import PlanningMonth
from scheduling.domain.planning_unit import PlanningUnitId
from scheduling.domain.shift import ShiftId


class WishType(StrEnum):
    FREE_DAY = "free_day"
    FREE_SHIFT = "free_shift"
    PREFERRED_DAY = "preferred_day"
    PREFERRED_SHIFT = "preferred_shift"


class Wish(SchedulingBaseModel):
    employee_id: EmployeeId
    planning_unit_id: PlanningUnitId

    date: Date
    type: WishType
    shift_id: ShiftId | None = None

    @model_validator(mode="after")
    def validate_wish(self) -> Self:
        if self.type in {WishType.FREE_SHIFT, WishType.PREFERRED_SHIFT} and self.shift_id is None:
            raise ValueError(f"{self.type} wish requires shift_id.")

        if self.type in {WishType.FREE_DAY, WishType.PREFERRED_DAY} and self.shift_id is not None:
            raise ValueError(f"{self.type} wish must not define shift_id.")

        return self


class WeeklyWish(SchedulingBaseModel):
    employee_id: EmployeeId
    planning_unit_id: PlanningUnitId
    planning_month: PlanningMonth

    weekday: int  # weekday: 1=Monday, 7=Sunday
    type: WishType
    shift_id: ShiftId | None = None

    # TODO: Validator fehlt noch
