from enum import StrEnum
from typing import Final

from app.domain.core import NonEmptyStr, PositiveId, SchedulingBaseModel

EmployeeId = PositiveId


class StaffLevel(StrEnum):
    """Reduced staffing level used by demand and solver logic.

    This is mapped from TimeOffice source data such as Berufe/Qualis.
    The solver should depend on this enum, not on raw TimeOffice IDs.
    """

    PROFESSIONAL = "professional"
    ASSISTANT = "assistant"
    TRAINEE = "trainee"
    MFA = "mfa"  # Medizinische Fachangestellte

    @property
    def label(self) -> str:
        """The German name the chair's minimum staffing uses: Fachkraft, Hilfskraft, Azubi or MFA."""
        return _LABELS[self]


_LABELS: Final = {
    StaffLevel.PROFESSIONAL: "Fachkraft",
    StaffLevel.ASSISTANT: "Hilfskraft",
    StaffLevel.TRAINEE: "Azubi",
    StaffLevel.MFA: "MFA",
}


class Employee(SchedulingBaseModel):
    """Employee known to the scheduling dataset.

    The domain model intentionally does not expose raw TimeOffice profession or
    qualification IDs. The TimeOffice adapter maps those source details into the
    reduced solver-facing fields below.
    """

    employee_id: EmployeeId
    display_name: NonEmptyStr

    staff_level: StaffLevel


class EmployeeSummary(SchedulingBaseModel):
    """Who an employee is, for choosing one; monthly facts belong to an inspection."""

    employee_id: EmployeeId
    display_name: NonEmptyStr
