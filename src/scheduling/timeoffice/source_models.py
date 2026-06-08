from datetime import date as Date

from pydantic import BaseModel, Field

from src.scheduling.models.core import PlanningPeriod


class TimeOfficePlanSource(BaseModel):
    """TimeOffice plan metadata for one station/planning unit and period."""

    station_id: int = Field(gt=0)
    source_plan_id: int = Field(gt=0)
    source_planning_unit_id: int = Field(gt=0)

    station_name: str | None = None

    status_id: int | None = None
    planning_interval_id: int | None = None

    period: PlanningPeriod


class TimeOfficePlanEmployeeSource(BaseModel):
    """Employee assigned to a concrete TimeOffice monthly plan."""

    source_plan_employee_id: int = Field(gt=0)
    source_plan_id: int = Field(gt=0)

    station_id: int = Field(gt=0)
    employee_id: int = Field(gt=0)

    personnel_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    short_name: str | None = None

    source_profession_id: int | None = None

    valid_from: Date | None = None
    valid_until: Date | None = None

    is_substitute: bool | None = None
