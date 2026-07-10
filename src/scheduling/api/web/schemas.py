from pydantic import Field

from scheduling.domain.core import SchedulingBaseModel


class WishesAndBlockedEmployeeRequest(SchedulingBaseModel):
    key: int
    firstname: str | None = None
    name: str | None = None
    wish_days: tuple[int, ...] = Field(default_factory=tuple)
    wish_shifts: tuple[tuple[int, str], ...] = Field(default_factory=tuple)
    blocked_days: tuple[int, ...] = Field(default_factory=tuple)
    blocked_shifts: tuple[tuple[int, str], ...] = Field(default_factory=tuple)


class WishesAndBlockedDatabaseRequest(SchedulingBaseModel):
    employees: tuple[WishesAndBlockedEmployeeRequest, ...]


class CreateWishesAndBlockedRequest(SchedulingBaseModel):
    data: WishesAndBlockedEmployeeRequest


class SuccessResponse(SchedulingBaseModel):
    success: bool = True
