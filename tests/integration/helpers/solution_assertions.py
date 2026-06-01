import ast
from collections import Counter
from dataclasses import dataclass
from datetime import date

from src.employee import Employee
from src.shift import Shift
from tests.integration.helpers.solver_fixtures import MinStaffing

WEEKDAY_ABBREVIATIONS: dict[int, str] = {
    1: "Mo",
    2: "Di",
    3: "Mi",
    4: "Do",
    5: "Fr",
    6: "Sa",
    7: "So",
}


@dataclass(frozen=True)
class Assignment:
    employee_id: int
    day: date
    shift_id: int


def active_shift_assignments(solution_variables: dict[str, int]) -> list[Assignment]:
    assignments: list[Assignment] = []

    for variable_name, value in solution_variables.items():
        if value != 1:
            continue

        try:
            employee_id, day_value, shift_id = ast.literal_eval(variable_name)
        except (SyntaxError, ValueError):
            continue

        if not isinstance(employee_id, int):
            continue
        if not isinstance(day_value, str):
            continue
        if not isinstance(shift_id, int):
            continue

        assignments.append(
            Assignment(
                employee_id=employee_id,
                day=date.fromisoformat(day_value),
                shift_id=shift_id,
            )
        )

    return assignments


def assert_solution_found(status_name: str) -> None:
    assert status_name in {"FEASIBLE", "OPTIMAL"}, f"Expected feasible solver result, got {status_name}"


def assert_only_known_employees_assigned(assignments: list[Assignment], employees: list[Employee]) -> None:
    known_employee_ids = {employee.get_key() for employee in employees}
    assigned_employee_ids = {assignment.employee_id for assignment in assignments}

    assert assigned_employee_ids <= known_employee_ids, (
        f"Solution contains assignments for unknown employees: {sorted(assigned_employee_ids - known_employee_ids)}"
    )


def assert_no_more_than_one_shift_per_employee_day(assignments: list[Assignment]) -> None:
    counts = Counter((assignment.employee_id, assignment.day) for assignment in assignments)
    duplicates = {key: count for key, count in counts.items() if count > 1}

    assert not duplicates, f"Employees assigned to more than one shift per day: {duplicates}"


def assert_unavailable_employees_not_assigned(assignments: list[Assignment], employees: list[Employee]) -> None:
    employee_by_id = {employee.get_key(): employee for employee in employees}

    invalid_assignments = [
        assignment
        for assignment in assignments
        if assignment.day.day in employee_by_id[assignment.employee_id].vacation_days
        or employee_by_id[assignment.employee_id].unavailable(assignment.day)
    ]

    assert not invalid_assignments, f"Unavailable employees were assigned: {invalid_assignments}"


def assert_no_exclusive_shift_assigned(assignments: list[Assignment], shifts: list[Shift]) -> None:
    exclusive_shift_ids = {shift.get_id() for shift in shifts if shift.is_exclusive}
    invalid_assignments = [assignment for assignment in assignments if assignment.shift_id in exclusive_shift_ids]

    assert not invalid_assignments, (
        f"Exclusive/preplanned shifts leaked into generated assignments: {invalid_assignments}"
    )


def assert_min_staffing_is_covered(
    *,
    assignments: list[Assignment],
    employees: list[Employee],
    shifts: list[Shift],
    days: list[date],
    min_staffing: MinStaffing,
) -> None:
    employee_by_id = {employee.get_key(): employee for employee in employees}
    shift_by_id = {shift.get_id(): shift for shift in shifts}

    assignment_counts: Counter[tuple[str, date, str]] = Counter()

    for assignment in assignments:
        employee = employee_by_id[assignment.employee_id]
        shift = shift_by_id[assignment.shift_id]

        if shift.is_exclusive:
            continue

        assignment_counts[(employee.level, assignment.day, shift.abbreviation)] += 1

    mismatches: list[str] = []

    for employee_level, staffing_by_weekday in min_staffing.items():
        for day in days:
            weekday = WEEKDAY_ABBREVIATIONS[day.isoweekday()]
            required_by_shift = staffing_by_weekday[weekday]

            for shift_abbreviation, required_count in required_by_shift.items():
                actual_count = assignment_counts[(employee_level, day, shift_abbreviation)]

                if actual_count != required_count:
                    mismatches.append(
                        f"{employee_level} {day.isoformat()} {shift_abbreviation}: "
                        f"expected {required_count}, got {actual_count}"
                    )

    assert not mismatches, "Minimum staffing mismatches:\n" + "\n".join(mismatches)
