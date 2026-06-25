from calendar import monthrange
from datetime import date

from pydantic import Field, computed_field

from scheduling.domain import SchedulingBaseModel
from scheduling.domain.assignment import Assignment
from scheduling.domain.availability import Availability
from scheduling.domain.demand import DemandRequirement
from scheduling.domain.employee import Employee
from scheduling.domain.monthly_work_account import MonthlyWorkAccount
from scheduling.domain.plan import Plan
from scheduling.domain.planning_unit import PlanningUnit, PlanningUnitMembership
from scheduling.domain.shift import Shift
from scheduling.domain.sunday_work_history import EmployeeSundayWorkHistory
from scheduling.domain.wish import Wish


class PlanningMonth(SchedulingBaseModel):
    year: int = Field(ge=2000, le=2200)
    month: int = Field(ge=1, le=12)

    @computed_field
    @property
    def start(self) -> date:
        return date(self.year, self.month, 1)

    @computed_field
    @property
    def end(self) -> date:
        return date(
            self.year,
            self.month,
            monthrange(self.year, self.month)[1],
        )

    @property
    def label(self) -> str:
        return f"{self.year:04d}-{self.month:02d}"


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
