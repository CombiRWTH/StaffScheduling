from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class Demand(BaseModel):
    """Staffing need or optional coverage goal for a station/date/shift."""

    station_id: int = Field(gt=0)
    date: date
    shift_id: str

    required_count: int = Field(ge=0)

    required_group_id: str | None = None
    required_qualification_id: str | None = None

    demand_type: Literal["minimum", "optional"] = "minimum"
    priority: int = Field(default=0, ge=0)
    weight: int = Field(default=1, ge=0)
