from datetime import date as Date
from enum import StrEnum
from typing import Self

from pydantic import model_validator

from scheduling.domain.core import NonEmptyStr, PositiveId, SchedulingBaseModel
from scheduling.domain.employee import EmployeeId, StaffLevel

PlanningUnitId = PositiveId


class PlanningUnitKind(StrEnum):
    """Kind of planning unit used by the scheduling pipeline.

    STATION:
        Planning unit with staffing demand. The solver may assign employees
        into this unit.

    SHARED_POOL:
        Planning unit used as a possible cross-unit employee source. Marking a
        unit as SHARED_POOL never creates eligibility by itself. Eligibility
        still requires real membership rows.
    """

    STATION = "station"
    SHARED_POOL = "shared_pool"


class PlanningUnit(SchedulingBaseModel):
    """Stable organizational scheduling unit.

    This mirrors the TimeOffice concept "Planungseinheit". A planning unit can
    represent a station/ward or, if explicitly configured and backed by data, a
    shared/jump pool.
    """

    planning_unit_id: PlanningUnitId
    display_name: NonEmptyStr
    kind: PlanningUnitKind


class PlanningUnitMembership(SchedulingBaseModel):
    """Active employee membership interval in a PlanningUnit.

    This comes from TimeOffice `TPlanungseinheitenPersonal`.

    Multiple intervals for the same employee and planning unit are valid because
    eligibility can change inside the planning period.
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
