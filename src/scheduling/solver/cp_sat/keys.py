from datetime import date

from scheduling.domain.employee import EmployeeId, StaffLevel
from scheduling.domain.planning_unit import PlanningUnitId
from scheduling.domain.shift import ShiftId

type AssignmentVariableKey = tuple[EmployeeId, PlanningUnitId, date, ShiftId, StaffLevel]

type DemandKey = tuple[PlanningUnitId, date, ShiftId, StaffLevel]

type EmployeeDateKey = tuple[EmployeeId, date]
type MembershipKey = tuple[EmployeeId, PlanningUnitId]
