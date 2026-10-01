from datetime import date

from app.domain.employee import EmployeeId, StaffLevel
from app.domain.planning_unit import PlanningUnitId
from app.domain.shift import ShiftId

type AssignmentVariableKey = tuple[EmployeeId, PlanningUnitId, date, ShiftId, StaffLevel]

type DemandKey = tuple[PlanningUnitId, date, ShiftId, StaffLevel]

type EmployeeDateKey = tuple[EmployeeId, date]
type MembershipKey = tuple[EmployeeId, PlanningUnitId]
