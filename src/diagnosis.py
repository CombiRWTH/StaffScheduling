"""Infeasibility diagnosis for staff scheduling cases."""

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from src.diagnosis_config import (
    VALID_EMPLOYEE_LEVELS,
    CheckType,
    DiagnosisConfig,
    Severity,
)
from src.employee import Employee
from src.loader.filesystem_loader import FSLoader


@dataclass
class DataIssue:
    """Represents a single data issue found during diagnosis."""

    severity: Severity
    check_type: CheckType
    file: str
    message: str
    employee_key: int | None = None
    day: int | None = None
    shift: str | None = None
    field: str | None = None
    value: Any = None
    fix_suggestion: str | None = None


@dataclass
class DiagnosisResult:
    """Result of infeasibility diagnosis."""

    issues: list[DataIssue] = field(default_factory=list)
    error_count: int = 0
    warning_count: int = 0
    info_count: int = 0

    def add_issue(self, issue: DataIssue) -> None:
        """Add an issue to the result."""
        self.issues.append(issue)
        if issue.severity == Severity.ERROR:
            self.error_count += 1
        elif issue.severity == Severity.WARNING:
            self.warning_count += 1
        elif issue.severity == Severity.INFO:
            self.info_count += 1

    def has_errors(self) -> bool:
        """Check if any ERROR level issues were found."""
        return self.error_count > 0

    def is_likely_infeasible(self) -> bool:
        """Determine if the case is likely infeasible based on issues found."""
        return self.has_errors()


class InfeasibilityDiagnoser:
    """Diagnoses potential infeasibility causes in scheduling cases."""

    def __init__(self, case_id: int, start_date: date, end_date: date, config: DiagnosisConfig | None = None):
        """Initialize the diagnoser."""
        self.case_id = case_id
        self.start_date = start_date
        self.end_date = end_date
        self.config = config if config else DiagnosisConfig()
        self.case_path = Path(f"cases/{case_id}")
        self.result = DiagnosisResult()

        # Data containers
        self.employees: list[Employee] = []
        self.json_data: dict[str, Any] = {}

    def diagnose(self) -> DiagnosisResult:
        """Run full diagnosis and return results."""
        print(f"🔍 Diagnosing case {self.case_id} for period {self.start_date} to {self.end_date}...")

        # Step 1: Load and validate JSON structure
        if not self._load_json_files():
            return self.result

        # Step 2: Load employees (may fail if data is invalid)
        try:
            loader = FSLoader(self.case_id)
            self.employees = loader.get_employees()
        except Exception as e:
            self._add_issue(
                Severity.ERROR,
                CheckType.MALFORMED_JSON,
                "general",
                f"Failed to load employee data: {str(e)}",
                fix_suggestion="Check JSON syntax and structure in all case files",
            )
            return self.result

        # Step 3: Check target/actual working time feasibility (MAIN CHECK)
        self._check_working_time_feasibility()

        return self.result

    def _load_json_files(self) -> bool:
        """Load and validate JSON file structure."""
        required_files = [
            "employees.json",
            "target_working_minutes.json",
            "free_shifts_and_vacation_days.json",
            "minimal_number_of_staff.json",
        ]

        optional_files = [
            "employee_types.json",
            "general_settings.json",
            "shift_information.json",
            "wishes_and_blocked.json",
            "worked_sundays.json",
        ]

        # Check required files exist
        for filename in required_files:
            filepath = self.case_path / filename
            if not filepath.exists():
                self._add_issue(
                    Severity.ERROR,
                    CheckType.MISSING_KEY,
                    filename,
                    f"Required file not found: {filename}",
                    fix_suggestion=f"Create {filename} in cases/{self.case_id}/",
                )
                continue

            # Load and parse JSON
            try:
                with open(filepath, encoding="utf-8") as f:
                    self.json_data[filename] = json.load(f)
            except json.JSONDecodeError as e:
                self._add_issue(
                    Severity.ERROR,
                    CheckType.MALFORMED_JSON,
                    filename,
                    f"Invalid JSON syntax: {str(e)}",
                    fix_suggestion="Fix JSON syntax errors (check for missing commas, brackets, quotes)",
                )
                return False
            except Exception as e:
                self._add_issue(
                    Severity.ERROR,
                    CheckType.MALFORMED_JSON,
                    filename,
                    f"Error reading file: {str(e)}",
                )
                return False

        # Load optional files
        for filename in optional_files:
            filepath = self.case_path / filename
            if filepath.exists():
                try:
                    with open(filepath, encoding="utf-8") as f:
                        self.json_data[filename] = json.load(f)
                except Exception:
                    pass  # Optional files are not critical

        # Validate structure of each file
        self._validate_json_structure()

        return not self.result.has_errors()

    def _validate_json_structure(self) -> None:
        """Validate the structure of loaded JSON files."""
        # Validate employees.json
        if "employees.json" in self.json_data:
            data = self.json_data["employees.json"]
            if "employees" not in data:
                self._add_issue(
                    Severity.ERROR,
                    CheckType.MISSING_KEY,
                    "employees.json",
                    "Missing required key 'employees'",
                    fix_suggestion="Add 'employees' array to the JSON file",
                )
            elif not isinstance(data["employees"], list):
                self._add_issue(
                    Severity.ERROR,
                    CheckType.INVALID_TYPE,
                    "employees.json",
                    "'employees' must be an array",
                    fix_suggestion="Change 'employees' to be an array of employee objects",
                )

        # Validate target_working_minutes.json
        if "target_working_minutes.json" in self.json_data:
            data = self.json_data["target_working_minutes.json"]
            if "employees" not in data:
                self._add_issue(
                    Severity.ERROR,
                    CheckType.MISSING_KEY,
                    "target_working_minutes.json",
                    "Missing required key 'employees'",
                    fix_suggestion="Add 'employees' array to the JSON file",
                )

        # Validate minimal_number_of_staff.json
        if "minimal_number_of_staff.json" in self.json_data:
            data = self.json_data["minimal_number_of_staff.json"]
            for level in VALID_EMPLOYEE_LEVELS:
                if level not in data:
                    self._add_issue(
                        Severity.WARNING,
                        CheckType.MISSING_KEY,
                        "minimal_number_of_staff.json",
                        f"Missing employee level '{level}' in minimal staffing",
                        fix_suggestion=f"Add '{level}' object with weekday staffing requirements",
                    )

    def _check_working_time_feasibility(self) -> None:
        """Check if target working times are achievable."""
        if not self.employees:
            return

        # Calculate total days in planning period
        total_days = (self.end_date - self.start_date).days + 1

        # Tolerance constants (same as in TargetWorkingTimeConstraint)
        TOLERANCE = 460  # Upper and lower tolerance

        # Load target_working_minutes data for actual minutes check
        target_data = self.json_data.get("target_working_minutes.json", {})
        target_emp_data = {emp.get("key"): emp for emp in target_data.get("employees", [])}

        for emp in self.employees:
            if emp.hidden:
                continue  # Hidden employees don't have target constraints

            # Count vacation days and forbidden days
            vacation_days = len(emp.vacation_days)
            forbidden_days = len(emp._forbidden_days)

            # Calculate available working days (excluding both vacation and forbidden days)
            available_days = total_days - vacation_days - forbidden_days

            # Check if actual + planned minutes can meet target
            emp_target_data = target_emp_data.get(emp.get_key())
            if emp_target_data:
                target = emp_target_data.get("target", 0)
                actual = emp_target_data.get("actual", 0)

                # Calculate maximum possible minutes in this period with available days
                # Night shift (N) is longest at 565 minutes
                max_possible_in_period = available_days * 565

                # Calculate how many minutes can be achieved: actual + max_possible
                max_achievable_total = actual + max_possible_in_period

                # Check if the original target can be achieved at all
                if max_achievable_total + TOLERANCE < target:
                    shortage = target - max_achievable_total - TOLERANCE
                    self._add_issue(
                        Severity.ERROR,
                        CheckType.TARGET_MINUTES_UNACHIEVABLE,
                        "target_working_minutes.json",
                        f"Employee {emp.get_key()} ({emp.name}): target unachievable (target: {target:.0f} min"
                        + ", actual: {actual:.0f} min, max possible"
                        "in period: {max_possible_in_period:.0f} min, max achievable: {max_achievable_total:.0f} min, available days: {available_days}/{total_days})",
                        employee_key=emp.get_key(),
                        value={
                            "actual": actual,
                            "target": target,
                            "max_possible": max_possible_in_period,
                            "max_achievable": max_achievable_total,
                            "available_days": available_days,
                            "vacation_days": vacation_days,
                            "forbidden_days": forbidden_days,
                        },
                        fix_suggestion=f"Reduce target by {int(shortage)} minutes, reduce actual by {int(shortage)} minutes, or reduce"
                        + "vacation/forbidden days by {int(shortage / 565) + 1}",
                    )

                # Additionally check the adjusted target (for the planning period)
                adjusted_target = target * available_days / total_days
                remaining_needed = adjusted_target - actual

                # Check if actual already exceeds adjusted target for this period
                if actual > adjusted_target + TOLERANCE:
                    excess = actual - (adjusted_target + TOLERANCE)
                    self._add_issue(
                        Severity.WARNING,
                        CheckType.TARGET_MINUTES_UNACHIEVABLE,
                        "target_working_minutes.json",
                        f"Employee {emp.get_key()} ({emp.name}): actual minutes already exceed adjusted target for period"
                        + " (actual: {actual:.0f} min, adjusted target: {adjusted_target:.0f} min, excess: {excess:.0f} min)",
                        employee_key=emp.get_key(),
                        value={
                            "actual": actual,
                            "target": target,
                            "adjusted_target": adjusted_target,
                            "excess": excess,
                        },
                        fix_suggestion=f"Increase target by {int(excess)} minutes or reduce actual minutes",
                    )

    def _add_issue(
        self,
        severity: Severity,
        check_type: CheckType,
        file: str,
        message: str,
        employee_key: int | None = None,
        day: int | None = None,
        shift: str | None = None,
        field: str | None = None,
        value: Any = None,
        fix_suggestion: str | None = None,
    ) -> None:
        """Add an issue to the diagnosis result."""
        issue = DataIssue(
            severity=severity,
            check_type=check_type,
            file=file,
            message=message,
            employee_key=employee_key,
            day=day,
            shift=shift,
            field=field,
            value=value,
            fix_suggestion=fix_suggestion,
        )
        self.result.add_issue(issue)


def format_diagnosis_result(result: DiagnosisResult) -> str:
    """Format diagnosis result as colored terminal output."""
    # ANSI color codes
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    lines = []
    lines.append(f"\n{BOLD}{'=' * 80}{RESET}")
    lines.append(f"{BOLD}INFEASIBILITY DIAGNOSIS REPORT{RESET}")
    lines.append(f"{BOLD}{'=' * 80}{RESET}\n")

    # Summary
    if result.has_errors():
        verdict = f"{RED}{BOLD}❌ LIKELY INFEASIBLE{RESET}"
    elif result.warning_count > 0:
        verdict = f"{YELLOW}{BOLD}⚠️  POTENTIALLY INFEASIBLE{RESET}"
    else:
        verdict = f"{GREEN}{BOLD}✅ LIKELY FEASIBLE{RESET}"

    lines.append(f"Verdict: {verdict}\n")
    lines.append(
        f"Issues found: {RED}{result.error_count} errors{RESET}, "
        f"{YELLOW}{result.warning_count} warnings{RESET}, "
        f"{BLUE}{result.info_count} info{RESET}\n"
    )

    if not result.issues:
        lines.append(f"{GREEN}No issues detected. The case appears well-formed.{RESET}\n")
        return "\n".join(lines)

    # Group issues by severity and file
    errors_by_file = defaultdict(list)
    warnings_by_file = defaultdict(list)
    infos_by_file = defaultdict(list)

    for issue in result.issues:
        if issue.severity == Severity.ERROR:
            errors_by_file[issue.file].append(issue)
        elif issue.severity == Severity.WARNING:
            warnings_by_file[issue.file].append(issue)
        else:
            infos_by_file[issue.file].append(issue)

    # Print errors
    if errors_by_file:
        lines.append(f"{RED}{BOLD}ERRORS (Must Fix):{RESET}")
        lines.append(f"{RED}{'─' * 80}{RESET}")
        for file, issues in sorted(errors_by_file.items()):
            lines.append(f"\n{RED}{BOLD}📄 {file}{RESET}")
            for i, issue in enumerate(issues, 1):
                lines.append(f"  {i}. {RED}✗{RESET} {issue.message}")
                if issue.fix_suggestion:
                    lines.append(f"     {BOLD}Fix:{RESET} {issue.fix_suggestion}")
        lines.append("")

    # Print warnings
    if warnings_by_file:
        lines.append(f"{YELLOW}{BOLD}WARNINGS (Should Review):{RESET}")
        lines.append(f"{YELLOW}{'─' * 80}{RESET}")
        for file, issues in sorted(warnings_by_file.items()):
            lines.append(f"\n{YELLOW}{BOLD}📄 {file}{RESET}")
            for i, issue in enumerate(issues, 1):
                lines.append(f"  {i}. {YELLOW}⚠{RESET} {issue.message}")
                if issue.fix_suggestion:
                    lines.append(f"     {BOLD}Suggestion:{RESET} {issue.fix_suggestion}")
        lines.append("")

    # Print infos
    if infos_by_file:
        lines.append(f"{BLUE}{BOLD}INFO (For Reference):{RESET}")
        lines.append(f"{BLUE}{'─' * 80}{RESET}")
        for file, issues in sorted(infos_by_file.items()):
            lines.append(f"\n{BLUE}{BOLD}📄 {file}{RESET}")
            for i, issue in enumerate(issues, 1):
                lines.append(f"  {i}. {BLUE}ℹ{RESET} {issue.message}")
        lines.append("")

    lines.append(f"{BOLD}{'=' * 80}{RESET}\n")

    return "\n".join(lines)
