from enum import StrEnum

from scheduling.domain.core import NonEmptyStr, PositiveId, SchedulingBaseModel

EmployeeId = PositiveId


class StaffLevel(StrEnum):
    """Reduced staffing level used by demand and solver logic.

    This is mapped from TimeOffice source data such as Berufe/Qualis.
    The solver should depend on this enum, not on raw TimeOffice IDs.
    """

    PROFESSIONAL = "professional"  # Fachkraft
    ASSISTANT = "assistant"  # Hilfskraft
    TRAINEE = "trainee"  # Azubi


class Capability(StrEnum):
    """Special employee capability used by solver rules.

    Capabilities should come from validated TimeOffice data where possible.
    If a project requirement is not represented in TimeOffice, it should be
    added later through an explicit scenario input, not hidden in TimeOffice facts.
    """

    NIGHT_WATCH = "night_watch"
    ROUNDS = "rounds"


class Employee(SchedulingBaseModel):
    """Employee known to the scheduling dataset.

    The domain model intentionally does not expose raw TimeOffice profession or
    qualification IDs. The TimeOffice adapter maps those source details into the
    reduced solver-facing fields below.
    """

    employee_id: EmployeeId
    display_name: NonEmptyStr

    staff_level: StaffLevel
    capabilities: tuple[Capability, ...] = ()
