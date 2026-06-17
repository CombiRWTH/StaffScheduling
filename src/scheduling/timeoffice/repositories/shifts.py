from collections import defaultdict
from datetime import datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.models import SchedulingBaseModel, Shift
from scheduling.timeoffice.facts import TimeOfficeFacts, TimeOfficeShiftFact
from scheduling.timeoffice.repositories.types import CleanText, SourceInt, SourceNullableInt, TimeOfficeSourceRow


class _TimeOfficeShiftRow(TimeOfficeSourceRow):
    shift_id: SourceInt
    shift_code: CleanText
    shift_type_id: SourceInt

    segment_start: datetime | None = None
    segment_end: datetime | None = None
    segment_minutes: SourceNullableInt = None

    @model_validator(mode="after")
    def validate_segment_shape(self) -> Self:
        has_start = self.segment_start is not None
        has_end = self.segment_end is not None

        if has_start != has_end:
            raise ValueError(
                "Incomplete TimeOffice shift segment: "
                f"shift_id={self.shift_id} "
                f"segment_start={self.segment_start!r} "
                f"segment_end={self.segment_end!r}."
            )

        if self.segment_start is not None and self.segment_end is not None:
            if self.segment_end <= self.segment_start:
                raise ValueError(
                    "Invalid TimeOffice shift segment: "
                    f"shift_id={self.shift_id} "
                    f"segment_start={self.segment_start!r} "
                    f"segment_end={self.segment_end!r}."
                )

        if self.segment_minutes is not None and self.segment_minutes < 0:
            raise ValueError(
                "Invalid negative TimeOffice shift segment minutes: "
                f"shift_id={self.shift_id} "
                f"segment_minutes={self.segment_minutes!r}."
            )

        return self


class ShiftRepositoryResult(SchedulingBaseModel):
    shifts: tuple[Shift, ...]


class TimeOfficeShiftRepository:
    """Reads TimeOffice shifts and maps them to reduced scheduling shifts."""

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(self, *, connection: Connection) -> ShiftRepositoryResult:
        shift_ids = tuple(self._facts.shift_facts_by_id.keys())

        if not shift_ids:
            return ShiftRepositoryResult(shifts=())

        rows = self._fetch_rows(
            connection=connection,
            shift_ids=shift_ids,
        )

        shifts = self._map_rows(rows)

        self._validate_requested_shifts(
            requested_shift_ids=shift_ids,
            shifts=shifts,
        )

        return ShiftRepositoryResult(shifts=shifts)

    def _fetch_rows(
        self,
        *,
        connection: Connection,
        shift_ids: tuple[int, ...],
    ) -> tuple[_TimeOfficeShiftRow, ...]:
        query = text(
            """
            SELECT
                d.Prim AS shift_id,
                d.KurzBez AS shift_code,
                d.RefDienstTypen AS shift_type_id,

                sz.Kommt AS segment_start,
                sz.Geht AS segment_end,
                sz.Minuten AS segment_minutes
            FROM TDienste d
            LEFT JOIN TDiensteSollzeiten sz
                ON sz.RefDienste = d.Prim
            WHERE d.Prim IN :shift_ids
            ORDER BY
                d.Prim,
                sz.Kommt,
                sz.Geht
            """
        ).bindparams(bindparam("shift_ids", expanding=True))

        raw_rows = (
            connection.execute(
                query,
                {"shift_ids": shift_ids},
            )
            .mappings()
            .all()
        )

        return tuple(_TimeOfficeShiftRow.model_validate(row) for row in raw_rows)

    def _map_rows(self, rows: tuple[_TimeOfficeShiftRow, ...]) -> tuple[Shift, ...]:
        rows_by_shift_id = self._group_rows_by_shift_id(rows)

        return tuple(
            self._map_shift(
                shift_id=shift_id,
                rows=shift_rows,
                shift_fact=self._facts.shift_facts_by_id[shift_id],
            )
            for shift_id, shift_rows in sorted(rows_by_shift_id.items())
        )

    def _group_rows_by_shift_id(self, rows: tuple[_TimeOfficeShiftRow, ...]) -> dict[int, list[_TimeOfficeShiftRow]]:
        rows_by_shift_id: dict[int, list[_TimeOfficeShiftRow]] = defaultdict(list)

        for row in rows:
            rows_by_shift_id[row.shift_id].append(row)

        return dict(rows_by_shift_id)

    def _map_shift(
        self,
        *,
        shift_id: int,
        rows: list[_TimeOfficeShiftRow],
        shift_fact: TimeOfficeShiftFact,
    ) -> Shift:
        first_row = rows[0]

        source_code = first_row.shift_code

        if self._normalize_shift_code(source_code) != self._normalize_shift_code(shift_fact.expected_code):
            raise ValueError(
                "Unexpected TimeOffice shift code for known scheduling shift: "
                f"shift_id={shift_id} expected={shift_fact.expected_code!r} actual={source_code!r}."
            )

        if first_row.shift_type_id not in self._facts.work_shift_type_ids:
            raise ValueError(
                "Known scheduling shift is not configured as real work shift in TimeOffice: "
                f"shift_id={shift_id} shift_type_id={first_row.shift_type_id}."
            )

        segments = self._map_segments(rows=rows, shift_id=shift_id)

        start_at = segments[0][0]
        end_at = segments[-1][1]

        return Shift(
            shift_id=shift_id,
            code=source_code,
            kind=shift_fact.kind,
            staffing_role=shift_fact.staffing_role,
            start_minute=self._minute_of_day(start_at),
            end_minute=self._minute_of_day(end_at),
            net_work_minutes=self._net_work_minutes(segments),
        )

    def _map_segments(
        self, *, rows: list[_TimeOfficeShiftRow], shift_id: int
    ) -> tuple[tuple[datetime, datetime, int], ...]:
        segments: list[tuple[datetime, datetime, int]] = []

        for row in rows:
            if row.segment_start is None and row.segment_end is None:
                continue

            if row.segment_start is None or row.segment_end is None:
                raise ValueError(
                    "Invalid TimeOffice shift row after source-row validation: "
                    f"shift_id={shift_id} "
                    f"segment_start={row.segment_start!r} "
                    f"segment_end={row.segment_end!r}."
                )

            segments.append(
                (
                    row.segment_start,
                    row.segment_end,
                    row.segment_minutes or 0,
                )
            )

        if not segments:
            raise ValueError(f"No timing segments found for TimeOffice shift_id={shift_id}.")

        return tuple(segments)

    def _net_work_minutes(self, segments: tuple[tuple[datetime, datetime, int], ...]) -> int:
        source_minutes = sum(segment_minutes for _, _, segment_minutes in segments)

        if source_minutes > 0:
            return source_minutes

        return sum(int((end_at - start_at).total_seconds() // 60) for start_at, end_at, _ in segments)

    def _validate_requested_shifts(self, *, requested_shift_ids: tuple[int, ...], shifts: tuple[Shift, ...]) -> None:
        returned_shift_ids = {shift.shift_id for shift in shifts}
        missing_shift_ids = sorted(set(requested_shift_ids) - returned_shift_ids)

        if missing_shift_ids:
            raise ValueError(f"Missing TimeOffice shift definitions for shift_ids={missing_shift_ids}.")

    def _minute_of_day(self, value: datetime) -> int:
        return value.hour * 60 + value.minute

    def _normalize_shift_code(self, value: str) -> str:
        return value.strip().casefold()
