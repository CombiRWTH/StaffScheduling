from datetime import date as Date

from pydantic import Field

from scheduling.domain.core import SchedulingBaseModel
from scheduling.domain.employee import StaffLevel
from scheduling.domain.planning_unit import PlanningUnitId
from scheduling.domain.shift import ShiftId


class DemandRequirement(SchedulingBaseModel):
    """Hard minimum staffing demand for one planning unit, date, shift and staff level."""

    planning_unit_id: PlanningUnitId
    date: Date
    shift_id: ShiftId
    staff_level: StaffLevel
    required_count: int = Field(gt=0)
