from datetime import date as Date

from pydantic import Field

from src.scheduling.models.core import SchedulingBaseModel
from src.scheduling.models.employee import StaffLevel
from src.scheduling.models.planning_unit import PlanningUnitId
from src.scheduling.models.shift import ShiftId


class DemandRequirement(SchedulingBaseModel):
    """Hard minimum staffing demand for one planning unit, date, shift and staff level."""

    planning_unit_id: PlanningUnitId
    date: Date
    shift_id: ShiftId
    staff_level: StaffLevel
    required_count: int = Field(gt=0)
