import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from json import dump
from pathlib import Path
from typing import Any

from scheduling.domain import Assignment, AssignmentType, AvailabilityType, StaffLevel, WishType
from scheduling.domain.dataset import SchedulingDataset
from scheduling.domain.shift import ShiftId
from scheduling.solver.models import Solution, SolutionStatus
from scheduling.timeoffice.facts import (
    EARLY_F2_SHIFT_ID,
    INTERMEDIATE_T75_SHIFT_ID,
    LATE_S2_SHIFT_ID,
    MANAGEMENT_Z60_SHIFT_ID,
    NIGHT_N2_SHIFT_ID,
)

logger = logging.getLogger(__name__)

LEGACY_SHIFT_ID_BY_REFERENCE_SHIFT_ID: dict[ShiftId, int] = {
    EARLY_F2_SHIFT_ID: 0,
    INTERMEDIATE_T75_SHIFT_ID: 1,
    LATE_S2_SHIFT_ID: 2,
    NIGHT_N2_SHIFT_ID: 3,
    MANAGEMENT_Z60_SHIFT_ID: 4,
}

LEGACY_SHIFTS: tuple[dict[str, Any], ...] = (
    {"id": 0, "name": "Früh", "abbreviation": "F", "color": "#a8d51f", "duration": 460, "is_exclusive": False},
    {"id": 1, "name": "Zwischen", "abbreviation": "Z", "color": "#3a9ea1", "duration": 460, "is_exclusive": False},
    {"id": 2, "name": "Spät", "abbreviation": "S", "color": "#f69e17", "duration": 460, "is_exclusive": False},
    {"id": 3, "name": "Nacht", "abbreviation": "N", "color": "#225e62", "duration": 565, "is_exclusive": False},
    {
        "id": 4,
        "name": "Z60",
        "abbreviation": "Z",
        "color": "oklch(82.1% 0.087 285.6)",
        "duration": 360,
        "is_exclusive": True,
    },
    {"id": 5, "name": "F2_", "abbreviation": "F", "color": "#dadada", "duration": 460, "is_exclusive": True},
    {"id": 6, "name": "S2_", "abbreviation": "S", "color": "#dadada", "duration": 460, "is_exclusive": True},
    {"id": 7, "name": "N5", "abbreviation": "N", "color": "#dadada", "duration": 565, "is_exclusive": True},
)


@dataclass(frozen=True, slots=True)
class LegacySolutionExportPaths:
    solution_path: Path
    processed_solution_path: Path


class TimeOfficeSolutionWriter:
    """Allowed TimeOffice write surface for solver-generated assignments."""

    def __init__(
        self,
        *,
        legacy_solution_dir: Path | str = "found_solutions",
        processed_solution_dir: Path | str = "processed_solutions",
    ) -> None:
        self._legacy_solution_dir = Path(legacy_solution_dir)
        self._processed_solution_dir = Path(processed_solution_dir)

    def write_dry_run(self, solution: Solution) -> None:
        if solution.status not in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}:
            logger.info(
                "Skipping TimeOffice writeback dry-run because solution is not feasible: status=%s",
                solution.status.value,
            )
            return

        generated_assignments = _generated_assignments(solution)

        logger.info(
            "Running TimeOffice writeback dry-run: generated_assignments=%s",
            len(generated_assignments),
        )

        for assignment in generated_assignments:
            logger.debug(
                "Generated assignment for TimeOffice writeback dry-run: "
                "employee_id=%s planning_unit_id=%s date=%s shift_id=%s",
                assignment.employee_id,
                assignment.planning_unit_id,
                assignment.date.isoformat(),
                assignment.shift_id,
            )

        logger.info(
            "Finished TimeOffice writeback dry-run: generated_assignments=%s written=0",
            len(generated_assignments),
        )

    def write_legacy_format(
        self,
        *,
        dataset: SchedulingDataset,
        solution: Solution,
        solution_name: str,
    ) -> LegacySolutionExportPaths | None:
        if solution.status not in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}:
            logger.info(
                "Skipping legacy solution export because solution is not feasible: status=%s",
                solution.status.value,
            )
            return None

        processed_data = build_legacy_processed_solution_data(
            dataset=dataset,
            solution=solution,
            solution_name=solution_name,
            solution_file_names=self._legacy_solution_file_names(current_solution_name=solution_name),
        )
        solution_output_path = (self._legacy_solution_dir / f"{solution_name}.json").resolve()
        solution_output_path.parent.mkdir(parents=True, exist_ok=True)

        with solution_output_path.open("w") as file:
            dump(processed_data, file, indent=4)

        processed_output_path = (self._processed_solution_dir / f"{solution_name}_processed.json").resolve()
        processed_output_path.parent.mkdir(parents=True, exist_ok=True)

        with processed_output_path.open("w") as file:
            dump(processed_data, file, indent=4)

        logger.info(
            "Wrote legacy solution export: solution_path=%s processed_path=%s variables=%s assigned_variables=%s",
            solution_output_path,
            processed_output_path,
            len(processed_data["variables"]),
            sum(1 for value in processed_data["variables"].values() if value == 1),
        )

        return LegacySolutionExportPaths(
            solution_path=solution_output_path,
            processed_solution_path=processed_output_path,
        )

    def _legacy_solution_file_names(self, *, current_solution_name: str) -> list[str]:
        solution_file_names = sorted(
            path.stem for path in self._legacy_solution_dir.glob("solution_*.json") if path.is_file()
        )

        if current_solution_name not in solution_file_names:
            solution_file_names.append(current_solution_name)
            solution_file_names.sort()

        return solution_file_names


def build_legacy_solution_data(*, dataset: SchedulingDataset, solution: Solution) -> dict[str, Any]:
    variables = _legacy_variables(dataset=dataset, solution=solution)

    return {
        "variables": variables,
        "objective": 0.0,
    }


def build_legacy_processed_solution_data(
    *,
    dataset: SchedulingDataset,
    solution: Solution,
    solution_name: str,
    solution_file_names: list[str],
) -> dict[str, Any]:
    variables = _legacy_variables(dataset=dataset, solution=solution)
    employees = _legacy_employees(dataset)
    days = tuple(assignment_date.isoformat() for assignment_date in _planning_dates(dataset))
    wish_cells = _legacy_wish_cells(dataset=dataset, variables=variables)

    return {
        "solution_file_names": solution_file_names,
        "selected_solution_file_name": solution_name,
        "employees": employees,
        "days": days,
        "shifts": LEGACY_SHIFTS,
        "stats": _legacy_stats(variables=variables, employees=employees),
        "fulfilled_shift_wish_cells": wish_cells["fulfilled_shift_wish_cells"],
        "fulfilled_day_off_cells": wish_cells["fulfilled_day_off_cells"],
        "all_shift_wish_colors": wish_cells["all_shift_wish_colors"],
        "all_day_off_wish_cells": wish_cells["all_day_off_wish_cells"],
        "variables": variables,
    }


def _legacy_variables(*, dataset: SchedulingDataset, solution: Solution) -> dict[str, int]:
    assignments = _legacy_solution_assignments(dataset=dataset, solution=solution)
    assigned_days = {(assignment.employee_id, assignment.date) for assignment in assignments}

    variables = {
        _legacy_variable_key(employee.employee_id, assignment_date, legacy_shift_id): 0
        for employee in sorted(dataset.employees, key=lambda item: item.employee_id)
        for assignment_date in _planning_dates(dataset)
        for legacy_shift_id in range(8)
    }
    variables.update(
        {
            _legacy_employee_works_on_day_key(employee.employee_id, assignment_date): int(
                (employee.employee_id, assignment_date) in assigned_days
            )
            for employee in sorted(dataset.employees, key=lambda item: item.employee_id)
            for assignment_date in _planning_dates(dataset)
        }
    )

    for assignment in assignments:
        legacy_shift_id = LEGACY_SHIFT_ID_BY_REFERENCE_SHIFT_ID[assignment.shift_id]
        variables[_legacy_variable_key(assignment.employee_id, assignment.date, legacy_shift_id)] = 1

    return variables


def _legacy_employees(dataset: SchedulingDataset) -> list[dict[str, Any]]:
    monthly_accounts = {account.employee_id: account for account in dataset.monthly_work_accounts}
    wishes_by_employee = _wishes_by_employee(dataset)
    availability_by_employee = _availability_by_employee(dataset)

    employees: list[dict[str, Any]] = []

    for employee in sorted(dataset.employees, key=lambda item: item.employee_id):
        monthly_account = monthly_accounts.get(employee.employee_id)
        wishes = wishes_by_employee.get(employee.employee_id, [])
        availability = availability_by_employee.get(employee.employee_id, [])

        employees.append(
            {
                "id": employee.employee_id,
                "name": employee.display_name,
                "level": _legacy_staff_level(employee.staff_level),
                "target_working_time": monthly_account.target_minutes if monthly_account is not None else 0,
                "wishes": {
                    "shift_wishes": _legacy_shift_wishes(wishes),
                    "day_off_wishes": [wish.date.day for wish in wishes if wish.type == WishType.FREE_DAY],
                },
                "forbidden_days": [
                    item.date.day
                    for item in availability
                    if item.availability_type
                    in {AvailabilityType.UNAVAILABLE, AvailabilityType.TRAINING, AvailabilityType.FREE_DAY}
                ],
                "forbidden_shifts": _legacy_forbidden_shifts(availability),
                "vacation_days": [
                    item.date.day for item in availability if item.availability_type == AvailabilityType.VACATION
                ],
                "vacation_shifts": [],
                "hidden_actual_working_time": monthly_account.actual_minutes if monthly_account is not None else 0,
                "actual_working_time": monthly_account.actual_minutes if monthly_account is not None else 0,
            }
        )

    return employees


def _legacy_wish_cells(*, dataset: SchedulingDataset, variables: dict[str, int]) -> dict[str, Any]:
    wishes_by_employee = _wishes_by_employee(dataset)
    fulfilled_shift_wish_cells: list[list[int | str]] = []
    fulfilled_day_off_cells: list[list[int | str]] = []
    all_shift_wish_colors: dict[str, list[str]] = {}
    all_day_off_wish_cells: list[list[int | str]] = []

    for employee in sorted(dataset.employees, key=lambda item: item.employee_id):
        wishes = wishes_by_employee.get(employee.employee_id, [])
        day_off_wish_days = {wish.date.day for wish in wishes if wish.type == WishType.FREE_DAY}

        for assignment_date in _planning_dates(dataset):
            date_label = assignment_date.isoformat()
            cell = [employee.employee_id, date_label]

            if assignment_date.day in day_off_wish_days:
                all_day_off_wish_cells.append(cell)
                if not _employee_has_non_exclusive_assignment(
                    employee_id=employee.employee_id,
                    assignment_date=assignment_date,
                    variables=variables,
                ):
                    fulfilled_day_off_cells.append(cell)

            shift_wish_ids = [
                LEGACY_SHIFT_ID_BY_REFERENCE_SHIFT_ID[wish.shift_id]
                for wish in wishes
                if wish.type == WishType.FREE_SHIFT and wish.shift_id is not None and wish.date == assignment_date
            ]
            if not shift_wish_ids:
                continue

            all_shift_wish_colors[f"{employee.employee_id}-{date_label}"] = [
                _legacy_shift_color(legacy_shift_id) for legacy_shift_id in shift_wish_ids
            ]
            if assignment_date.day in day_off_wish_days:
                continue
            if all(
                variables.get(_legacy_variable_key(employee.employee_id, assignment_date, legacy_shift_id)) != 1
                for legacy_shift_id in shift_wish_ids
            ):
                fulfilled_shift_wish_cells.append(cell)

    return {
        "fulfilled_shift_wish_cells": fulfilled_shift_wish_cells,
        "fulfilled_day_off_cells": fulfilled_day_off_cells,
        "all_shift_wish_colors": all_shift_wish_colors,
        "all_day_off_wish_cells": all_day_off_wish_cells,
    }


def _legacy_stats(*, variables: dict[str, int], employees: list[dict[str, Any]]) -> dict[str, float]:
    parsed: dict[int, dict[date, int]] = {}
    employee_by_id = {employee["id"]: employee for employee in employees}

    for key, value in variables.items():
        if value != 1 or not key.startswith("("):
            continue

        employee_id_text, date_text, shift_id_text = key.removeprefix("(").removesuffix(")").split(", ")
        employee_id = int(employee_id_text)
        assignment_date = date.fromisoformat(date_text.strip("'"))
        shift_id = int(shift_id_text)
        parsed.setdefault(employee_id, {})[assignment_date] = shift_id

    forward_rotation_violations = 0
    consecutive_working_days_gt_5 = 0
    no_free_weekend = 0
    consecutive_night_shifts_gt_3 = 0
    total_overtime_hours = 0.0
    no_free_days_around_weekend = 0
    not_free_after_night_shift = 0
    total_wish_violations = 0

    for employee_id, schedule in parsed.items():
        days = sorted(schedule)
        shifts_assigned = list(schedule.values())
        employee = employee_by_id[employee_id]

        forward_rotation_violations += _forward_rotation_violations(shifts_assigned)
        consecutive_working_days_gt_5 += _consecutive_working_day_violations(days)
        no_free_weekend += int(any(day.weekday() in {5, 6} for day in days))
        consecutive_night_shifts_gt_3 += _consecutive_night_shift_violations(shifts_assigned)
        total_overtime_hours += _overtime_hours(shifts_assigned, employee["target_working_time"])
        no_free_days_around_weekend += _no_free_days_around_weekend(schedule)
        not_free_after_night_shift += _not_free_after_night_shift(schedule)
        total_wish_violations += _total_wish_violations(employee=employee, schedule=schedule)

    return {
        "forward_rotation_violations": forward_rotation_violations,
        "consecutive_working_days_gt_5": consecutive_working_days_gt_5,
        "no_free_weekend": no_free_weekend,
        "consecutive_night_shifts_gt_3": consecutive_night_shifts_gt_3,
        "total_overtime_hours": round(total_overtime_hours, 2),
        "no_free_days_around_weekend": no_free_days_around_weekend,
        "not_free_after_night_shift": not_free_after_night_shift,
        "violated_wish_total": total_wish_violations,
    }


def _legacy_solution_assignments(*, dataset: SchedulingDataset, solution: Solution) -> tuple[Assignment, ...]:
    selected_planning_unit_ids = {planning_unit.planning_unit_id for planning_unit in dataset.planning_units}
    planned_assignments = tuple(
        assignment
        for assignment in dataset.assignments
        if assignment.assignment_type == AssignmentType.PLANNED
        and assignment.planning_unit_id in selected_planning_unit_ids
    )

    return (*planned_assignments, *_generated_assignments(solution))


def _planning_dates(dataset: SchedulingDataset) -> Iterable[date]:
    current_date = dataset.planning_month.start

    while current_date <= dataset.planning_month.end:
        yield current_date
        current_date += timedelta(days=1)


def _legacy_variable_key(employee_id: int, assignment_date: date, legacy_shift_id: int) -> str:
    return f"({employee_id}, '{assignment_date.isoformat()}', {legacy_shift_id})"


def _legacy_employee_works_on_day_key(employee_id: int, assignment_date: date) -> str:
    return f"e:{employee_id}_d:{assignment_date.isoformat()}"


def _legacy_staff_level(staff_level: StaffLevel) -> str:
    return {
        StaffLevel.PROFESSIONAL: "Fachkraft",
        StaffLevel.ASSISTANT: "Hilfskraft",
        StaffLevel.TRAINEE: "Azubi",
    }[staff_level]


def _legacy_shift_abbreviation(legacy_shift_id: int) -> str:
    return str(LEGACY_SHIFTS[legacy_shift_id]["abbreviation"])


def _legacy_shift_color(legacy_shift_id: int) -> str:
    return str(LEGACY_SHIFTS[legacy_shift_id]["color"])


def _wishes_by_employee(dataset: SchedulingDataset):
    wishes_by_employee: dict[int, list[Any]] = {}
    for wish in dataset.wishes:
        wishes_by_employee.setdefault(wish.employee_id, []).append(wish)
    return wishes_by_employee


def _availability_by_employee(dataset: SchedulingDataset):
    availability_by_employee: dict[int, list[Any]] = {}
    for availability in dataset.availability:
        availability_by_employee.setdefault(availability.employee_id, []).append(availability)
    return availability_by_employee


def _legacy_forbidden_shifts(availability: list[Any]) -> list[list[int | str]]:
    forbidden_shifts: list[list[int | str]] = []
    all_legacy_shift_ids = set(range(8))

    for item in availability:
        if item.availability_type != AvailabilityType.AVAILABLE_ONLY or item.shift_ids is None:
            continue

        available_legacy_shift_ids = {LEGACY_SHIFT_ID_BY_REFERENCE_SHIFT_ID[shift_id] for shift_id in item.shift_ids}
        for legacy_shift_id in sorted(all_legacy_shift_ids - available_legacy_shift_ids):
            forbidden_shifts.append([item.date.day, _legacy_shift_abbreviation(legacy_shift_id)])

    return forbidden_shifts


def _legacy_shift_wishes(wishes: list[Any]) -> list[list[int | str]]:
    return [
        [wish.date.day, _legacy_shift_abbreviation(LEGACY_SHIFT_ID_BY_REFERENCE_SHIFT_ID[wish.shift_id])]
        for wish in wishes
        if wish.type == WishType.FREE_SHIFT and wish.shift_id is not None
    ]


def _employee_has_non_exclusive_assignment(
    *, employee_id: int, assignment_date: date, variables: dict[str, int]
) -> bool:
    return any(
        variables.get(_legacy_variable_key(employee_id, assignment_date, legacy_shift_id)) == 1
        for legacy_shift_id in range(4)
    )


def _forward_rotation_violations(shifts_assigned: list[int]) -> int:
    valid_shifts = [shift_id for shift_id in shifts_assigned if shift_id in {0, 2, 3}]
    return sum(1 for index in range(len(valid_shifts) - 1) if valid_shifts[index + 1] < valid_shifts[index])


def _consecutive_working_day_violations(days: list[date]) -> int:
    if not days:
        return 0

    streak = 1
    violations = 0
    for index in range(1, len(days)):
        if (days[index] - days[index - 1]).days == 1:
            streak += 1
            continue

        if streak > 5:
            violations += 1
        streak = 1

    if streak > 5:
        violations += 1

    return violations


def _consecutive_night_shift_violations(shifts_assigned: list[int]) -> int:
    night_streak = 0
    violations = 0
    for shift_id in shifts_assigned:
        if shift_id == 2:
            night_streak += 1
            continue

        if night_streak > 3:
            violations += 1
        night_streak = 0

    if night_streak > 3:
        violations += 1

    return violations


def _overtime_hours(shifts_assigned: list[int], target_minutes: int) -> float:
    actual_minutes = sum(int(LEGACY_SHIFTS[shift_id]["duration"]) for shift_id in shifts_assigned)
    return max((actual_minutes - target_minutes) / 60, 0)


def _no_free_days_around_weekend(schedule: dict[date, int]) -> int:
    violations = 0
    for assignment_date in schedule:
        if assignment_date.weekday() == 4 and (assignment_date + timedelta(days=1)) in schedule:
            violations += 1
        elif assignment_date.weekday() == 5 and (assignment_date + timedelta(days=1)) in schedule:
            violations += 1
    return violations


def _not_free_after_night_shift(schedule: dict[date, int]) -> int:
    violations = 0
    for assignment_date, shift_id in schedule.items():
        if shift_id == 3 and (
            assignment_date + timedelta(days=1) in schedule or assignment_date + timedelta(days=2) in schedule
        ):
            violations += 1
    return violations


def _total_wish_violations(*, employee: dict[str, Any], schedule: dict[date, int]) -> int:
    violations = 0
    shift_wishes: dict[int, list[str]] = {}
    for day, abbreviation in employee["wishes"]["shift_wishes"]:
        shift_wishes.setdefault(day, []).append(abbreviation)

    for assignment_date, shift_id in schedule.items():
        if _legacy_shift_abbreviation(shift_id) in shift_wishes.get(assignment_date.day, []):
            violations += 1

    for day in employee["wishes"]["day_off_wishes"]:
        if any(assignment_date.day == day for assignment_date in schedule):
            violations += 1

    return violations


def _generated_assignments(solution: Solution) -> tuple[Assignment, ...]:
    return tuple(
        assignment for assignment in solution.assignments if assignment.assignment_type == AssignmentType.GENERATED
    )
