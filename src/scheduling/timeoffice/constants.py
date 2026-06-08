from enum import IntEnum


class TimeOfficePlanStatus(IntEnum):
    """Known TimeOffice plan status ids."""

    TARGET_PLANNING = 20
    ACTUAL = 50
    COMPLETED = 70
    SETTLED = 80


class TimeOfficePlanningInterval(IntEnum):
    """Known TimeOffice planning interval ids."""

    MONTHLY = 1
    ANNUAL = 3
