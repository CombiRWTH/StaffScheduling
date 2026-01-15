"""Configuration for infeasibility diagnosis checks."""

from enum import Enum


class Severity(Enum):
    """Severity levels for diagnosis issues."""

    ERROR = "ERROR"  # Critical data errors that prevent solving
    WARNING = "WARNING"  # Potential issues that may cause infeasibility
    INFO = "INFO"  # Informational notes about data


class CheckType(Enum):
    """Types of validation checks."""

    MISSING_KEY = "missing_key"
    INVALID_TYPE = "invalid_type"
    MALFORMED_JSON = "malformed_json"
    TARGET_MINUTES_UNACHIEVABLE = "target_minutes_unachievable"


VALID_EMPLOYEE_LEVELS = {"Azubi", "Fachkraft", "Hilfskraft"}
