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
