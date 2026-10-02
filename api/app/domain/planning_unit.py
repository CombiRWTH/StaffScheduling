from collections.abc import Iterable
from datetime import date as Date
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from app.domain.core import NonEmptyStr, PositiveId, SchedulingBaseModel
from app.domain.employee import EmployeeId, StaffLevel

PlanningUnitId = PositiveId


class PlanningUnitType(StrEnum):
    """Type of planning unit. Every unit is a pool of employees; the type decides whether it is planned.

    STATION:
        Has staffing demand and receives assignments.

    JUMPER_POOL:
        Home of employees who stand in at stations. By definition it has no
        demand and receives no assignments. Its home membership never creates
        eligibility; a replacement membership at the station does.
    """

    STATION = "station"
    JUMPER_POOL = "jumper_pool"


class PlanningUnit(SchedulingBaseModel):
    """Stable organizational scheduling unit.

    This mirrors the TimeOffice concept "Planungseinheit": a station or a jumper pool.
    """

    planning_unit_id: PlanningUnitId
    display_name: NonEmptyStr
    type: PlanningUnitType


class PlanningUnitMembership(SchedulingBaseModel):
    """Active employee membership interval in a PlanningUnit.

    This comes from TimeOffice `TPlanungseinheitenPersonal`.

    Multiple intervals for the same employee and planning unit are valid because
    eligibility can change inside the planning month.
    """

    planning_unit_id: PlanningUnitId
    employee_id: EmployeeId

    valid_from: Date
    valid_until: Date | None = None

    staff_level: StaffLevel

    is_home: bool
    is_replacement: bool

    def active_on(self, day: Date) -> bool:
        return self.valid_from <= day and (self.valid_until is None or day <= self.valid_until)

    @model_validator(mode="after")
    def validate_membership(self) -> Self:
        if self.valid_until is not None and self.valid_from > self.valid_until:
            raise ValueError("PlanningUnitMembership.valid_from must be before or equal to valid_until.")

        return self


def home_unit_id(memberships: Iterable[PlanningUnitMembership], employee_id: int, day: Date) -> int | None:
    """The employee's home station or jumper pool on `day`: their assignment origin.

    None when the employee has no active membership that day; more than one active home is ambiguous
    and raises ValueError, so an origin is never guessed.
    """
    active = [row for row in memberships if row.employee_id == employee_id and row.active_on(day)]
    homes = {row.planning_unit_id for row in active if row.is_home}
    if not active:
        return None
    if len(homes) != 1:
        raise ValueError(f"Employee {employee_id} requires one evidenced home origin on {day}.")
    return homes.pop()
