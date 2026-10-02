from app.domain.assignment import Assignment
from app.domain.availability import Availability
from app.domain.core import SchedulingBaseModel
from app.domain.demand import DemandRequirement
from app.domain.employee import Employee
from app.domain.monthly_work_account import MonthlyWorkAccount
from app.domain.plan import Plan
from app.domain.planning_month import PlanningMonth
from app.domain.planning_unit import PlanningUnit, PlanningUnitMembership
from app.domain.shift import Shift
from app.domain.sunday_work_history import EmployeeSundayWorkHistory
from app.domain.wish import Wish


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

    assignments: tuple[Assignment, ...] = ()
    availability: tuple[Availability, ...] = ()

    monthly_work_accounts: tuple[MonthlyWorkAccount, ...] = ()
