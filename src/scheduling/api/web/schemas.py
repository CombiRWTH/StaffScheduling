from pydantic import Field

from scheduling.domain.core import SchedulingBaseModel


class WishesAndBlockedEmployeeRequest(SchedulingBaseModel):
    key: int
    firstname: str | None = None
    name: str | None = None

    blocked_days: tuple[int, ...] = Field(default_factory=tuple)
    blocked_shifts: tuple[tuple[int, str], ...] = Field(default_factory=tuple)

    wish_days: tuple[int, ...] = Field(default_factory=tuple)
    wish_shifts: tuple[tuple[int, str], ...] = Field(default_factory=tuple)

    work_days: tuple[int, ...] = Field(default_factory=tuple)
    work_shifts: tuple[tuple[int, str], ...] = Field(default_factory=tuple)


class WishesAndBlockedDatabaseRequest(SchedulingBaseModel):
    employees: tuple[WishesAndBlockedEmployeeRequest, ...]


class CreateWishesAndBlockedRequest(SchedulingBaseModel):
    data: WishesAndBlockedEmployeeRequest


class UpdateMinimalStaffRequest(SchedulingBaseModel):
    data: dict[str, dict[str, dict[str, int]]]


class WeightsRequestData(SchedulingBaseModel):
    after_night: int = Field(ge=0)
    consecutive_days: int = Field(ge=0)
    consecutive_nights: int = Field(ge=0)
    fairness: int = Field(ge=0)
    free_weekend: int = Field(ge=0)
    hidden: int = Field(ge=0)
    overtime: int = Field(ge=0)
    rotate: int = Field(ge=0)
    second_weekend: int = Field(ge=0)
    wishes: int = Field(ge=0)


class UpdateWeightsRequest(SchedulingBaseModel):
    data: WeightsRequestData


class SuccessResponse(SchedulingBaseModel):
    success: bool = True
