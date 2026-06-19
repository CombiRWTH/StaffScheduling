from datetime import date as Date
from typing import Self

from pydantic import model_validator

from scheduling.domain.assignment import Assignment
from scheduling.domain.availability import Availability
from scheduling.domain.core import SchedulingBaseModel
from scheduling.domain.demand import DemandRequirement
from scheduling.domain.employee import Employee
from scheduling.domain.monthly_work_account import MonthlyWorkAccount
from scheduling.domain.plan import Plan, PlanParticipant
from scheduling.domain.planning_unit import PlanningUnit, PlanningUnitMembership
from scheduling.domain.shift import Shift
from scheduling.domain.sunday_work_history import EmployeeSundayWorkHistory
from scheduling.domain.wish import Wish


class PlanningPeriod(SchedulingBaseModel):
    """Inclusive planning period for one scheduling dataset."""

    start: Date
    end: Date

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        if self.start > self.end:
            raise ValueError(f"PlanningPeriod.start must be before or equal to end: {self.start} > {self.end}")

        return self

    def contains(self, date: Date) -> bool:
        return self.start <= date <= self.end


class SchedulingDataset(SchedulingBaseModel):
    """Clean scheduling dataset aligned with TimeOffice planning concepts.

    This is not solver input yet. Repositories and small transformation functions
    build this reduced model from TimeOffice. Solver-specific indexes and
    OR-Tools variables are derived later.
    """

    period: PlanningPeriod

    planning_units: tuple[PlanningUnit, ...]
    plans: tuple[Plan, ...]
    shifts: tuple[Shift, ...] = ()
    demand_requirements: tuple[DemandRequirement, ...] = ()

    employees: tuple[Employee, ...] = ()
    plan_participants: tuple[PlanParticipant, ...] = ()
    planning_unit_memberships: tuple[PlanningUnitMembership, ...] = ()
    sunday_work_history: tuple[EmployeeSundayWorkHistory, ...] = ()
    wishes: tuple[Wish, ...] = ()

    assignments: tuple[Assignment, ...] = ()
    availability: tuple[Availability, ...] = ()

    monthly_work_accounts: tuple[MonthlyWorkAccount, ...] = ()
