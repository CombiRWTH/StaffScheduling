"""The portable bundle of one monthly run: input.json, result.json, schedule.csv and employees.csv.

The files are readable, solvable and checkable without TimeOffice. A result names the SHA-256 of the
exact input.json bytes it was solved from, so a pair can be verified with the standard library. Every
`ScheduleBundle` is a validated pair: the format, the pairing, a found schedule whose references exist,
and a stored schedule check equal to an independent re-check. CSV tables are derived from the pair and
never read back.
"""

import csv
import io
import json
import platform
from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property
from hashlib import sha256
from importlib.metadata import version
from typing import Any, Final, Literal, Self

from pydantic import BaseModel, Field, ValidationError, model_validator

from app.domain import (
    POLICY,
    CalendarDay,
    PlanningMonth,
    Rule,
    ScheduleCheck,
    ScheduleTables,
    SchedulingBaseModel,
    SchedulingDataset,
    check_schedule,
    month_calendar,
    schedule_tables,
)
from app.domain.schedule import DutyRow, EmployeeRow
from app.solver.models import Solution

FORMAT_VERSION = 1
INPUT_FILE: Final = "input.json"
RESULT_FILE: Final = "result.json"
SCHEDULE_FILE: Final = "schedule.csv"
EMPLOYEES_FILE: Final = "employees.csv"
FILES = (INPUT_FILE, RESULT_FILE, SCHEDULE_FILE, EMPLOYEES_FILE)
type FileName = Literal["input.json", "result.json", "schedule.csv", "employees.csv"]


class ScheduleInput(SchedulingBaseModel):
    """input.json: everything one full-month run reads; no TimeOffice plan, wish or credential."""

    format_version: Literal[1]
    timezone: Literal["Europe/Berlin"]
    calendar: tuple[CalendarDay, ...]
    """Every date of the month with its ISO weekday and NRW public holiday; must equal the application's."""
    dataset: SchedulingDataset

    @model_validator(mode="after")
    def validate_calendar(self) -> Self:
        if self.calendar != month_calendar(self.dataset.planning_month):
            raise ValueError("The calendar is not the NRW calendar of the planning month.")
        return self

    @classmethod
    def of(cls, dataset: SchedulingDataset) -> Self:
        return cls(
            format_version=FORMAT_VERSION,
            timezone="Europe/Berlin",
            calendar=month_calendar(dataset.planning_month),
            dataset=dataset,
        )


class InputReference(SchedulingBaseModel):
    file: Literal["input.json"]
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    """Hex SHA-256 of the exact bytes of the input file."""


class RuntimeVersions(SchedulingBaseModel):
    """The runtime that solved; the lockfiles and the commit identify the rest of the software."""

    python: str
    ortools: str
    pydantic: str


class ScheduleResult(SchedulingBaseModel):
    """result.json: the solution of the paired input, with its effective configuration and schedule check."""

    format_version: Literal[1]
    planning_month: PlanningMonth
    input: InputReference
    solution: Solution
    versions: RuntimeVersions


class BundleProblem(StrEnum):
    """Why a pair of files is not a bundle."""

    MALFORMED = "malformed"
    MISMATCH = "mismatch"
    NO_SCHEDULE = "no_schedule"
    REFERENCES = "references"
    CHECK = "check"


class InvalidBundle(ValueError):
    def __init__(self, problem: BundleProblem, message: str) -> None:
        super().__init__(message)
        self.problem = problem


@dataclass(frozen=True)
class ScheduleBundle:
    input: ScheduleInput
    result: ScheduleResult
    input_json: bytes
    """The input file exactly as digested."""
    check: ScheduleCheck
    """The independent re-check, equal to the stored one."""

    @classmethod
    def solved(cls, input_json: bytes, solution: Solution) -> Self:
        """The bundle of a solution found for `input_json`; raises InvalidBundle like `read`."""
        schedule_input = read_input(input_json)
        result = ScheduleResult(
            format_version=FORMAT_VERSION,
            planning_month=schedule_input.dataset.planning_month,
            input=InputReference(file=INPUT_FILE, sha256=sha256(input_json).hexdigest()),
            solution=solution,
            versions=RuntimeVersions(
                python=platform.python_version(), ortools=version("ortools"), pydantic=version("pydantic")
            ),
        )
        return cls._validated(schedule_input, result, input_json)

    @classmethod
    def read(cls, input_json: bytes, result_json: bytes) -> Self:
        """Validate a pair of files; raises InvalidBundle naming the first problem."""
        schedule_input = read_input(input_json)
        return cls._validated(schedule_input, _parse(ScheduleResult, RESULT_FILE, result_json), input_json)

    @classmethod
    def _validated(cls, schedule_input: ScheduleInput, result: ScheduleResult, input_json: bytes) -> Self:
        dataset, solution = schedule_input.dataset, result.solution
        if result.input.sha256 != sha256(input_json).hexdigest():
            raise InvalidBundle(BundleProblem.MISMATCH, f"{RESULT_FILE} was solved from another {INPUT_FILE}.")
        if result.planning_month != dataset.planning_month:
            raise InvalidBundle(BundleProblem.MISMATCH, f"{RESULT_FILE} names another planning month.")
        if solution.check is None:
            raise InvalidBundle(BundleProblem.NO_SCHEDULE, f"{RESULT_FILE} has no schedule ({solution.status}).")
        if solution.configuration.policy != POLICY:
            raise InvalidBundle(BundleProblem.CHECK, f"{RESULT_FILE} was solved with other rule settings.")
        check = check_schedule(dataset, solution.assignments)
        if any(finding.rule == Rule.INPUT for finding in check.findings):
            raise InvalidBundle(
                BundleProblem.REFERENCES,
                f"{RESULT_FILE} has assignments of unknown employees, stations or shifts, outside the month or twice.",
            )
        if check != solution.check:
            raise InvalidBundle(BundleProblem.CHECK, f"The schedule check in {RESULT_FILE} differs from a re-check.")
        return cls(schedule_input, result, input_json, check)

    @cached_property
    def tables(self) -> ScheduleTables:
        return schedule_tables(self.input.dataset, self.result.solution.assignments)

    @cached_property
    def files(self) -> dict[FileName, bytes]:
        """All four files; input.json keeps its digested bytes."""
        return {
            INPUT_FILE: self.input_json,
            RESULT_FILE: to_json(self.result),
            SCHEDULE_FILE: _csv(DutyRow, self.tables.duties),
            EMPLOYEES_FILE: _csv(EmployeeRow, self.tables.employees),
        }


def to_json(model: BaseModel) -> bytes:
    """Indented JSON without derived fields, so it parses back into the same model."""
    return (model.model_dump_json(indent=2, round_trip=True) + "\n").encode()


def read_input(input_json: bytes) -> ScheduleInput:
    return _parse(ScheduleInput, INPUT_FILE, input_json)


def _parse[T: BaseModel](model: type[T], name: str, data: bytes) -> T:
    try:
        return model.model_validate_json(data)
    except ValidationError as error:
        first = error.errors(include_url=False)[0]
        where = ".".join(str(part) for part in first["loc"])
        raise InvalidBundle(
            BundleProblem.MALFORMED, f"{name} is invalid at {where or 'top level'}: {first['msg']}"
        ) from error


def _csv(model: type[SchedulingBaseModel], rows: tuple[SchedulingBaseModel, ...]) -> bytes:
    """UTF-8 CSV with one header row: true/false booleans, empty cells for absent values, JSON arrays as cells."""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(model.model_fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _cell(value) for key, value in row.model_dump(mode="json", round_trip=True).items()})
    return buffer.getvalue().encode()


def _cell(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    if isinstance(value, list | dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)
