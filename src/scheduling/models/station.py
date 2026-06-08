from pydantic import BaseModel, Field


class Station(BaseModel):
    """Hospital station or source planning unit."""

    station_id: int = Field(gt=0)
    name: str | None = None
    source_planning_unit_id: int | None = None
