from datetime import date as Date

from app.domain.core import SchedulingBaseModel
from app.domain.employee import EmployeeId, StaffLevel
from app.domain.planning_unit import PlanningUnitId
from app.domain.shift import ShiftId


class Assignment(SchedulingBaseModel):
    """One employee's duty: a shift starting on `date` at a station.

    `staff_level` is the qualification the duty is credited as towards demand; it comes from the
    employee's membership at that station, which can differ from their employee-level qualification.
    Its key is (employee_id, date, planning_unit_id, shift_id).
    """

    employee_id: EmployeeId
    date: Date
    planning_unit_id: PlanningUnitId
    shift_id: ShiftId
    staff_level: StaffLevel
