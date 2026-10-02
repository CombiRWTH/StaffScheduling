from datetime import date as Date
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from app.domain.core import SchedulingBaseModel
from app.domain.employee import EmployeeId
from app.domain.shift import ShiftId


class WishType(StrEnum):
    FREE_DAY = "free_day"
    FREE_SHIFT = "free_shift"
    PREFERRED_DAY = "preferred_day"
    PREFERRED_SHIFT = "preferred_shift"


# Wishes for time off; the others ask for a duty. Generation scores the two groups apart.
FREE_WISHES = frozenset({WishType.FREE_DAY, WishType.FREE_SHIFT})


class WishEntry(SchedulingBaseModel):
    """What a wish asks for, without saying whose or when."""

    type: WishType
    shift_id: ShiftId | None = None

    @model_validator(mode="after")
    def validate_wish(self) -> Self:
        if self.type in {WishType.FREE_SHIFT, WishType.PREFERRED_SHIFT} and self.shift_id is None:
            raise ValueError(f"{self.type} wish requires shift_id.")

        if self.type in {WishType.FREE_DAY, WishType.PREFERRED_DAY} and self.shift_id is not None:
            raise ValueError(f"{self.type} wish must not define shift_id.")

        return self


class Wish(WishEntry):
    """An employee's soft preference for one date at any station; at most one per employee and date.

    Generation considers it as one objective tier (see `OBJECTIVES`); it never binds.
    """

    employee_id: EmployeeId
    date: Date
