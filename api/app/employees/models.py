from app.domain import (
    Availability,
    EmployeeId,
    MonthlyWorkAccount,
    NonEmptyStr,
    PlanningMonth,
    PlanningUnit,
    PlanningUnitMembership,
    SchedulingBaseModel,
    StaffLevel,
)
from app.domain.monthly_work_account import WorkCredit


class EmployeeMonthEvidence(SchedulingBaseModel):
    employee_id: EmployeeId
    credit_details: tuple[WorkCredit, ...]
    hard_restrictions: tuple[Availability, ...]
    source: NonEmptyStr


class EmployeeInspection(SchedulingBaseModel):
    employee_id: EmployeeId
    display_name: NonEmptyStr
    staff_level: StaffLevel
    memberships: tuple[PlanningUnitMembership, ...]
    account: MonthlyWorkAccount
    hard_restrictions: tuple[Availability, ...]
    restrictions_source: NonEmptyStr


class PlanningInspection(SchedulingBaseModel):
    planning_month: PlanningMonth
    selected_station_ids: tuple[int, ...]
    planning_units: tuple[PlanningUnit, ...]
    employees: tuple[EmployeeInspection, ...]


class PlanningOptions(SchedulingBaseModel):
    planning_month: PlanningMonth
    planning_units: tuple[PlanningUnit, ...]
