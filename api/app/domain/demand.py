from datetime import date as Date

from pydantic import Field

from app.domain.core import SchedulingBaseModel
from app.domain.employee import StaffLevel
from app.domain.planning_unit import PlanningUnitId
from app.domain.shift import ShiftId


class DemandRequirement(SchedulingBaseModel):
    """Hard minimum staffing demand for one planning unit, date, shift and staff level."""

    planning_unit_id: PlanningUnitId
    date: Date
    shift_id: ShiftId
    staff_level: StaffLevel
    required_count: int = Field(gt=0)
