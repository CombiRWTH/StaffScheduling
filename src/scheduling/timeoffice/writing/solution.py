import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from json import dump
from pathlib import Path
from typing import Any

from sqlalchemy import Connection, bindparam, text

from scheduling.domain import Assignment, AssignmentType, AvailabilityType, PlanningMonth, StaffLevel, WishType
from scheduling.domain.dataset import SchedulingDataset
from scheduling.domain.shift import ShiftId
from scheduling.solver.models import Solution, SolutionStatus
from scheduling.timeoffice.facts import (
    EARLY_SHIFT_ID,
    INTERMEDIATE_SHIFT_ID,
    LATE_SHIFT_ID,
    NIGHT_SHIFT_ID,
    TimeOfficeFacts,
)

logger = logging.getLogger(__name__)

LEGACY_SHIFT_ID_BY_REFERENCE_SHIFT_ID: dict[ShiftId, int] = {
    EARLY_SHIFT_ID: 0,
    INTERMEDIATE_SHIFT_ID: 1,
    LATE_SHIFT_ID: 2,
    NIGHT_SHIFT_ID: 3,
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


@dataclass(frozen=True, slots=True)
class TimeOfficeShiftSegment:
    time_source_shift_id: int
    start_time: time
    end_time: time
    end_day_offset: int
    minutes: int


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

    def replace_solution_assignments(
        self,
        *,
        connection: Connection,
        dataset: SchedulingDataset,
        solution: Solution,
        facts: TimeOfficeFacts,
    ) -> None:
        if solution.status not in {SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE}:
            logger.info(
                "Skipping TimeOffice DB write because solution is not feasible: status=%s",
                solution.status.value,
            )
            return

        generated_assignments = _generated_assignments(solution)

        logger.info(
            "Replacing TimeOffice solution assignments: generated_assignments=%s",
            len(generated_assignments),
        )

        self._delete_solution_rows(
            connection=connection,
            dataset=dataset,
        )

        if not generated_assignments:
            logger.info("Deleted existing TimeOffice solution rows; no generated assignments to insert.")
            return

        time_source_shift_ids = tuple(
            sorted(
                {
                    self._time_source_shift_id(
                        reference_shift_id=assignment.shift_id,
                        facts=facts,
                    )
                    for assignment in generated_assignments
                }
            )
        )

        shift_segments = self._read_shift_segments(
            connection=connection,
            time_source_shift_ids=time_source_shift_ids,
        )

        parameters = self._insert_parameters(
            connection=connection,
            assignments=generated_assignments,
            shift_segments=shift_segments,
            facts=facts,
            planning_month=dataset.planning_month,
        )

        self._insert_solution_rows(
            connection=connection,
            parameters=parameters,
        )

        logger.info(
            "Replaced TimeOffice solution assignments: assignments=%s inserted_rows=%s",
            len(generated_assignments),
            len(parameters),
        )

    def _delete_solution_rows(
        self,
        *,
        connection: Connection,
        dataset: SchedulingDataset,
    ) -> None:
        planning_unit_ids = tuple(sorted(planning_unit.planning_unit_id for planning_unit in dataset.planning_units))

        if not planning_unit_ids:
            return

        query = text(
            """
                DELETE FROM TPlanPersonalKommtGeht
                WHERE RefPlanungseinheiten IN :planning_unit_ids
                  AND CONVERT(date, Datum) BETWEEN :start AND :end
                  AND ISNULL(Wunschdienst, 0) = 0
                  AND RefDienste IS NOT NULL
                  AND RefgAbw IS NULL
                  AND RefDienstAbw IS NULL
                  AND BereitVon IS NULL
                  AND BereitBis IS NULL
                """
        ).bindparams(bindparam("planning_unit_ids", expanding=True))

        connection.execute(
            query,
            {
                "planning_unit_ids": planning_unit_ids,
                "start": dataset.planning_month.start,
                "end": dataset.planning_month.end,
            },
        )

    def _read_shift_segments(
        self,
        *,
        connection: Connection,
        time_source_shift_ids: tuple[int, ...],
    ) -> dict[int, tuple[TimeOfficeShiftSegment, ...]]:
        if not time_source_shift_ids:
            return {}

        query = text(
            """
                SELECT
                    RefDienste AS time_source_shift_id,
                    Kommt AS start_datetime,
                    Geht AS end_datetime,
                    Minuten AS minutes
                FROM TDiensteSollzeiten
                WHERE RefDienste IN :time_source_shift_ids
                ORDER BY RefDienste, Kommt
                """
        ).bindparams(bindparam("time_source_shift_ids", expanding=True))

        rows = (
            connection.execute(
                query,
                {"time_source_shift_ids": time_source_shift_ids},
            )
            .mappings()
            .all()
        )

        segments_by_shift_id: dict[int, list[TimeOfficeShiftSegment]] = {}

        for row in rows:
            time_source_shift_id = int(row["time_source_shift_id"])
            start_datetime = row["start_datetime"]
            end_datetime = row["end_datetime"]

            if not isinstance(start_datetime, datetime):
                raise ValueError(
                    f"Unexpected Kommt value for time_source_shift_id={time_source_shift_id}: {start_datetime!r}"
                )

            if not isinstance(end_datetime, datetime):
                raise ValueError(
                    f"Unexpected Geht value for time_source_shift_id={time_source_shift_id}: {end_datetime!r}"
                )

            end_day_offset = (end_datetime.date() - start_datetime.date()).days

            segments_by_shift_id.setdefault(time_source_shift_id, []).append(
                TimeOfficeShiftSegment(
                    time_source_shift_id=time_source_shift_id,
                    start_time=start_datetime.time(),
                    end_time=end_datetime.time(),
                    end_day_offset=end_day_offset,
                    minutes=int(row["minutes"]),
                )
            )

        missing_shift_ids = sorted(set(time_source_shift_ids) - set(segments_by_shift_id))
        if missing_shift_ids:
            raise ValueError(f"No TDiensteSollzeiten found for time_source_shift_ids={missing_shift_ids}.")

        return {shift_id: tuple(segments) for shift_id, segments in segments_by_shift_id.items()}

    def _time_source_shift_id(
        self,
        *,
        reference_shift_id: int,
        facts: TimeOfficeFacts,
    ) -> int:
        time_source_shift_id = facts.time_source_shift_id_by_reference_shift_id.get(reference_shift_id)

        if time_source_shift_id is None:
            raise ValueError(f"No TimeOffice time-source shift configured for reference_shift_id={reference_shift_id}.")

        return time_source_shift_id

    def _insert_parameters(
        self,
        *,
        connection: Connection,
        assignments: tuple[Assignment, ...],
        shift_segments: dict[int, tuple[TimeOfficeShiftSegment, ...]],
        facts: TimeOfficeFacts,
        planning_month: PlanningMonth,
    ) -> list[dict[str, object]]:
        plan_id_by_planning_unit_id: dict[int, int] = {}
        status_id_by_plan_id: dict[int, int] = {}
        sequence_number_by_key: dict[tuple[int, int, date], int] = {}
        profession_id_by_employee_id: dict[int, int] = {}

        parameters: list[dict[str, object]] = []

        for assignment in assignments:
            if assignment.planning_unit_id not in plan_id_by_planning_unit_id:
                plan_id_by_planning_unit_id[assignment.planning_unit_id] = self._find_target_plan_id(
                    connection=connection,
                    planning_unit_id=assignment.planning_unit_id,
                    planning_month=planning_month,
                )

            plan_id = plan_id_by_planning_unit_id[assignment.planning_unit_id]

            if plan_id not in status_id_by_plan_id:
                status_id_by_plan_id[plan_id] = self._find_plan_status_id(
                    connection=connection,
                    plan_id=plan_id,
                )

            if assignment.employee_id not in profession_id_by_employee_id:
                profession_id_by_employee_id[assignment.employee_id] = self._find_profession_id(
                    connection=connection,
                    employee_id=assignment.employee_id,
                )

            time_source_shift_id = self._time_source_shift_id(
                reference_shift_id=assignment.shift_id,
                facts=facts,
            )

            segments = shift_segments.get(time_source_shift_id)
            if segments is None:
                raise ValueError(f"No shift segments found for time_source_shift_id={time_source_shift_id}.")

            for segment in segments:
                sequence_key = (
                    plan_id,
                    assignment.employee_id,
                    assignment.date,
                )

                if sequence_key not in sequence_number_by_key:
                    sequence_number_by_key[sequence_key] = self._next_sequence_number(
                        connection=connection,
                        plan_id=plan_id,
                        employee_id=assignment.employee_id,
                        date_value=assignment.date,
                    )

                sequence_number = sequence_number_by_key[sequence_key]
                sequence_number_by_key[sequence_key] += 1

                start_datetime = datetime.combine(
                    assignment.date,
                    segment.start_time,
                )
                end_datetime = datetime.combine(
                    assignment.date + timedelta(days=segment.end_day_offset),
                    segment.end_time,
                )

                if end_datetime <= start_datetime:
                    end_datetime += timedelta(days=1)

                parameters.append(
                    {
                        "plan_id": plan_id,
                        "employee_id": assignment.employee_id,
                        "assignment_date": assignment.date,
                        "status_id": status_id_by_plan_id[plan_id],
                        "sequence_number": sequence_number,
                        "shift_id": assignment.shift_id,
                        "profession_id": profession_id_by_employee_id[assignment.employee_id],
                        "planning_unit_id": assignment.planning_unit_id,
                        "start_datetime": start_datetime,
                        "end_datetime": end_datetime,
                        "minutes": segment.minutes,
                    }
                )

        return parameters

    def _insert_solution_rows(
        self,
        *,
        connection: Connection,
        parameters: list[dict[str, object]],
    ) -> None:
        if not parameters:
            return

        query = text(
            """
            INSERT INTO TPlanPersonalKommtGeht (
                RefPlan,
                RefPersonal,
                Datum,
                RefStati,
                lfdNr,
                RefgAbw,
                RefDienste,
                RefBerufe,
                RefPlanungseinheiten,
                VonZeit,
                BisZeit,
                RefDienstAbw,
                Minuten,
                Info,
                RefEinsatzArten,
                Wunschdienst,
                BereitVon,
                BereitBis
            )
            VALUES (
                :plan_id,
                :employee_id,
                :assignment_date,
                :status_id,
                :sequence_number,
                NULL,
                :shift_id,
                :profession_id,
                :planning_unit_id,
                :start_datetime,
                :end_datetime,
                NULL,
                :minutes,
                NULL,
                NULL,
                0,
                NULL,
                NULL
            )
            """
        )

        connection.execute(query, parameters)

    def _find_target_plan_id(
        self,
        *,
        connection: Connection,
        planning_unit_id: int,
        planning_month: PlanningMonth,
    ) -> int:
        query = text(
            """
            SELECT TOP 1
                p.Prim AS plan_id
            FROM TPlan p
            WHERE p.RefPlanungseinheiten = :planning_unit_id
              AND p.RefPlanungsIntervalle = 1
              AND CONVERT(date, p.VonDat) = :start
              AND CONVERT(date, p.BisDat) = :end
            ORDER BY p.Prim DESC
            """
        )

        row = (
            connection.execute(
                query,
                {
                    "planning_unit_id": planning_unit_id,
                    "start": planning_month.start,
                    "end": planning_month.end,
                },
            )
            .mappings()
            .first()
        )

        if row is None:
            raise ValueError(
                f"No TimeOffice plan found for planning_unit_id={planning_unit_id}, "
                f"planning_month={planning_month.year}-{planning_month.month:02d}."
            )

        return int(row["plan_id"])

    def _find_plan_status_id(
        self,
        *,
        connection: Connection,
        plan_id: int,
    ) -> int:
        query = text(
            """
            SELECT RefStati AS status_id
            FROM TPlan
            WHERE Prim = :plan_id
            """
        )

        row = (
            connection.execute(
                query,
                {"plan_id": plan_id},
            )
            .mappings()
            .first()
        )

        if row is None:
            raise ValueError(f"No TimeOffice plan status found for plan_id={plan_id}.")

        return int(row["status_id"])

    def _find_profession_id(
        self,
        *,
        connection: Connection,
        employee_id: int,
    ) -> int:
        query = text(
            """
            SELECT RefBerufe AS profession_id
            FROM TPersonal
            WHERE Prim = :employee_id
              AND RefBerufe IS NOT NULL
            """
        )

        row = (
            connection.execute(
                query,
                {"employee_id": employee_id},
            )
            .mappings()
            .first()
        )

        if row is None:
            raise ValueError(f"No TimeOffice profession found for employee_id={employee_id}.")

        return int(row["profession_id"])

    def _next_sequence_number(
        self,
        *,
        connection: Connection,
        plan_id: int,
        employee_id: int,
        date_value: date,
    ) -> int:
        query = text(
            """
            SELECT COALESCE(MAX(pkg.lfdNr), 0) + 1 AS next_sequence_number
            FROM TPlanPersonalKommtGeht pkg
            WHERE pkg.RefPlan = :plan_id
              AND pkg.RefPersonal = :employee_id
              AND CONVERT(date, pkg.Datum) = :date_value
            """
        )

        row = (
            connection.execute(
                query,
                {
                    "plan_id": plan_id,
                    "employee_id": employee_id,
                    "date_value": date_value,
                },
            )
            .mappings()
            .one()
        )

        return int(row["next_sequence_number"])


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
