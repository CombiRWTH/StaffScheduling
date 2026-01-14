"""Configuration for infeasibility diagnosis checks."""

from enum import Enum


class Severity(Enum):
    """Severity levels for diagnosis issues."""

    ERROR = "ERROR"  # Critical data errors that prevent solving
    WARNING = "WARNING"  # Potential issues that may cause infeasibility
    INFO = "INFO"  # Informational notes about data


class CheckType(Enum):
    """Types of validation checks."""

    # JSON structure checks
    MISSING_KEY = "missing_key"
    INVALID_TYPE = "invalid_type"
    MALFORMED_JSON = "malformed_json"

    # Domain validation
    INVALID_SHIFT_CODE = "invalid_shift_code"
    INVALID_DAY_NUMBER = "invalid_day_number"
    NEGATIVE_WORKING_TIME = "negative_working_time"
    INVALID_EMPLOYEE_LEVEL = "invalid_employee_level"
    INVALID_WEEKDAY = "invalid_weekday"

    # Cross-file consistency
    EMPLOYEE_KEY_MISMATCH = "employee_key_mismatch"
    UNKNOWN_SHIFT_CODE = "unknown_shift_code"
    INVALID_QUALIFICATION_REF = "invalid_qualification_ref"

    # Constraint feasibility
    INSUFFICIENT_STAFF_POOL = "insufficient_staff_pool"
    IMPOSSIBLE_WORKING_TIME = "impossible_working_time"
    VACATION_PLANNED_SHIFT_CONFLICT = "vacation_planned_shift_conflict"
    PLANNED_FORBIDDEN_CONFLICT = "planned_forbidden_conflict"
    INSUFFICIENT_WEEKEND_COVERAGE = "insufficient_weekend_coverage"
    INSUFFICIENT_QUALIFIED_STAFF = "insufficient_qualified_staff"
    EXCESSIVE_VACATION_DAYS = "excessive_vacation_days"
    IMPOSSIBLE_REST_TIME = "impossible_rest_time"
    TARGET_MINUTES_UNACHIEVABLE = "target_minutes_unachievable"


# Default severity levels for each check type
DEFAULT_SEVERITIES: dict[CheckType, Severity] = {
    # JSON structure - always errors
    CheckType.MISSING_KEY: Severity.ERROR,
    CheckType.INVALID_TYPE: Severity.WARNING,
    CheckType.MALFORMED_JSON: Severity.ERROR,
    # Domain validation - always errors
    CheckType.INVALID_SHIFT_CODE: Severity.ERROR,
    CheckType.INVALID_DAY_NUMBER: Severity.ERROR,
    CheckType.NEGATIVE_WORKING_TIME: Severity.ERROR,
    CheckType.INVALID_EMPLOYEE_LEVEL: Severity.ERROR,
    CheckType.INVALID_WEEKDAY: Severity.ERROR,
    # Cross-file consistency - errors
    CheckType.EMPLOYEE_KEY_MISMATCH: Severity.ERROR,
    CheckType.UNKNOWN_SHIFT_CODE: Severity.WARNING,  # Might be intentional
    CheckType.INVALID_QUALIFICATION_REF: Severity.ERROR,
    # Constraint feasibility - errors/warnings
    CheckType.INSUFFICIENT_STAFF_POOL: Severity.ERROR,
    CheckType.IMPOSSIBLE_WORKING_TIME: Severity.ERROR,
    CheckType.VACATION_PLANNED_SHIFT_CONFLICT: Severity.ERROR,
    CheckType.PLANNED_FORBIDDEN_CONFLICT: Severity.ERROR,
    CheckType.INSUFFICIENT_WEEKEND_COVERAGE: Severity.WARNING,
    CheckType.INSUFFICIENT_QUALIFIED_STAFF: Severity.ERROR,
    CheckType.EXCESSIVE_VACATION_DAYS: Severity.WARNING,
    CheckType.IMPOSSIBLE_REST_TIME: Severity.WARNING,
    CheckType.TARGET_MINUTES_UNACHIEVABLE: Severity.ERROR,
}


# Valid shift codes
VALID_SHIFT_CODES: set[str] = {"F", "S", "N", "Z", "Z60", "F2_", "S2_", "N5"}

# Valid employee levels
VALID_EMPLOYEE_LEVELS: set[str] = {"Azubi", "Fachkraft", "Hilfskraft"}

# Valid weekday names (German)
VALID_WEEKDAYS: set[str] = {"Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"}

# Shift name to code mapping
SHIFT_NAME_TO_CODE: dict[str, str] = {
    "Early": "F",
    "Intermediate": "Z",
    "Late": "S",
    "Night": "N",
}

# Required JSON files for a case
REQUIRED_FILES = [
    "employees.json",
    "target_working_minutes.json",
    "free_shifts_and_vacation_days.json",
    "minimal_number_of_staff.json",
]

# Optional JSON files
OPTIONAL_FILES = [
    "employee_types.json",
    "general_settings.json",
    "shift_information.json",
    "wishes_and_blocked.json",
    "worked_sundays.json",
]


class DiagnosisConfig:
    """Configuration for diagnosis checks with customizable severity levels."""

    def __init__(self, severities: dict[CheckType, Severity] | None = None):
        """Initialize with custom or default severities."""
        self.severities = severities if severities else DEFAULT_SEVERITIES.copy()

    def get_severity(self, check_type: CheckType) -> Severity:
        """Get severity level for a check type."""
        return self.severities.get(check_type, Severity.WARNING)

    def set_severity(self, check_type: CheckType, severity: Severity) -> None:
        """Set custom severity level for a check type."""
        self.severities[check_type] = severity

    def is_error(self, check_type: CheckType) -> bool:
        """Check if a check type is configured as ERROR severity."""
        return self.get_severity(check_type) == Severity.ERROR

    def is_warning(self, check_type: CheckType) -> bool:
        """Check if a check type is configured as WARNING severity."""
        return self.get_severity(check_type) == Severity.WARNING

    def is_info(self, check_type: CheckType) -> bool:
        """Check if a check type is configured as INFO severity."""
        return self.get_severity(check_type) == Severity.INFO
