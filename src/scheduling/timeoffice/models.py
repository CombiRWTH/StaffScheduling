from pathlib import Path

from pydantic import BaseModel, field_validator

from src.scheduling.models.core import PlanningPeriod


class FetchStationsRequest(BaseModel):
    """Request to provide scheduling data for one or more TimeOffice stations.

    If use_cache is true, cached StationMonthData is attempted first. If cache
    data is missing or invalid, the service falls back to database reads.
    """

    station_ids: tuple[int, ...]
    period: PlanningPeriod
    use_cache: bool = False

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


class TimeOfficeSourceData(BaseModel):
    """Raw TimeOffice source data read from the database.

    Current iteration: shallow placeholder.

    Later this should hold typed source-record collections. It must stay
    TimeOffice-facing and must not become the canonical scheduling model.
    """

    station_ids: tuple[int, ...]
    period: PlanningPeriod


class CacheWriteResult(BaseModel):
    """Result of writing one station-month cache payload."""

    station_id: int
    period: PlanningPeriod
    cache_directory: Path
