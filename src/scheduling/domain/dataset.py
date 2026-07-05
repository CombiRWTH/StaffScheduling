from scheduling.domain import SchedulingBaseModel
from scheduling.domain.assignment import Assignment
from scheduling.domain.availability import Availability
from scheduling.domain.demand import DemandRequirement
from scheduling.domain.employee import Employee
from scheduling.domain.monthly_work_account import MonthlyWorkAccount
from scheduling.domain.plan import Plan
from scheduling.domain.planning_month import PlanningMonth
from scheduling.domain.planning_unit import PlanningUnit, PlanningUnitMembership
from scheduling.domain.shift import Shift
from scheduling.domain.sunday_work_history import EmployeeSundayWorkHistory
from scheduling.domain.wish import WeeklyWish, Wish


class SchedulingDataset(SchedulingBaseModel):
    """Clean scheduling dataset aligned with TimeOffice planning concepts.

    This is not solver input yet. Repositories and small transformation functions
    build this reduced model from TimeOffice. Solver-specific indexes and
    OR-Tools variables are derived later.
    """

    planning_month: PlanningMonth

    planning_units: tuple[PlanningUnit, ...]
    plans: tuple[Plan, ...]
    shifts: tuple[Shift, ...] = ()
    demand_requirements: tuple[DemandRequirement, ...] = ()

    employees: tuple[Employee, ...] = ()
    planning_unit_memberships: tuple[PlanningUnitMembership, ...] = ()
    sunday_work_history: tuple[EmployeeSundayWorkHistory, ...] = ()
    wishes: tuple[Wish, ...] = ()
    weekly_wishes: tuple[WeeklyWish, ...]

    assignments: tuple[Assignment, ...] = ()
    availability: tuple[Availability, ...] = ()

    monthly_work_accounts: tuple[MonthlyWorkAccount, ...] = ()
