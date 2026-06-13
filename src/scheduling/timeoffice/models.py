from pydantic import BaseModel, field_validator

from src.scheduling.models.core import PlanningPeriod


class FetchStationsRequest(BaseModel):
    """Request to provide scheduling data for one or more TimeOffice stations."""

    station_ids: tuple[int, ...]
    period: PlanningPeriod

    @field_validator("station_ids")
    @classmethod
    def station_ids_must_not_be_empty(cls, station_ids: tuple[int, ...]) -> tuple[int, ...]:
        if not station_ids:
            raise ValueError("At least one station id is required.")

        return station_ids

    @field_validator("station_ids")
    @classmethod
    def station_ids_must_be_positive(cls, station_ids: tuple[int, ...]) -> tuple[int, ...]:
        invalid_station_ids = [station_id for station_id in station_ids if station_id <= 0]

        if invalid_station_ids:
            raise ValueError(f"Station ids must be positive: {invalid_station_ids}")

        return station_ids
