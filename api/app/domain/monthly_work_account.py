from datetime import date as Date
from typing import Literal, Self

from pydantic import NonNegativeInt, computed_field, model_validator

from app.domain.core import NonEmptyStr, SchedulingBaseModel
from app.domain.employee import EmployeeId


class WorkCredit(SchedulingBaseModel):
    date: Date
    minutes: NonNegativeInt
    kind: Literal["approved_absence", "trusted_work"]
    source: NonEmptyStr


class MonthlyWorkAccount(SchedulingBaseModel):
    employee_id: EmployeeId
    target_minutes: NonNegativeInt
    actual_minutes: NonNegativeInt | None = None
    # Dated credits of the month; empty means nothing is credited.
    credit_details: tuple[WorkCredit, ...] = ()

    @computed_field
    @property
    def credited_minutes(self) -> int:
        return sum(credit.minutes for credit in self.credit_details)

    @model_validator(mode="after")
    def validate_credits(self) -> Self:
        keys = {(credit.date, credit.kind, credit.source) for credit in self.credit_details}
        if len(keys) != len(self.credit_details):
            raise ValueError("Duplicate work credits.")
        return self
