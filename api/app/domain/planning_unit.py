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

    @model_validator(mode="after")
    def validate_membership(self) -> Self:
        if self.valid_until is not None and self.valid_from > self.valid_until:
            raise ValueError("PlanningUnitMembership.valid_from must be before or equal to valid_until.")

        return self
