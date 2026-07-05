from pydantic import Field

from scheduling.domain.core import SchedulingBaseModel


class AvailabilityEmployeeRequest(SchedulingBaseModel):
    key: int
    firstname: str | None = None
    name: str | None = None
    availability_days: tuple[int, ...] = Field(default_factory=tuple)
    unavailability_days: tuple[int, ...] = Field(default_factory=tuple)


class AvailabilityDatabaseRequest(SchedulingBaseModel):
    employees: tuple[AvailabilityEmployeeRequest, ...]


class UpdateAvailabilityRequest(SchedulingBaseModel):
    data: AvailabilityDatabaseRequest


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


class UpdateWishesAndBlockedRequest(SchedulingBaseModel):
    data: WishesAndBlockedDatabaseRequest


class SuccessResponse(SchedulingBaseModel):
    success: bool = True
