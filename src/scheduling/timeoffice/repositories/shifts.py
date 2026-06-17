from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime as DateTime

from sqlalchemy import Connection, bindparam, text
from sqlalchemy.engine import RowMapping

from src.scheduling.models import SchedulingBaseModel, Shift
from src.scheduling.timeoffice.facts import TimeOfficeFacts, TimeOfficeShiftFact
from src.scheduling.timeoffice.repositories.helpers import (
    clean_text,
    normalize_code,
    required,
    to_datetime,
    to_non_negative_int,
)


class ShiftRepositoryResult(SchedulingBaseModel):
    shifts: tuple[Shift, ...]


class TimeOfficeShiftRepository:
    """Reads TimeOffice shifts and maps them to reduced scheduling shifts."""

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
    ) -> ShiftRepositoryResult:
        shift_ids = tuple(int(shift_fact.source_shift_id) for shift_fact in self._facts.shift_facts)

        if not shift_ids:
            return ShiftRepositoryResult(shifts=())

        rows = tuple(
            connection.execute(
                self._query(),
                {"shift_ids": shift_ids},
            )
            .mappings()
            .all()
        )

        shifts = self._map_rows(rows)
        self._validate_requested_shifts(
            requested_shift_ids=shift_ids,
            shifts=shifts,
        )

        return ShiftRepositoryResult(shifts=shifts)

    def _query(self):
        return text(
            """
            SELECT
                d.Prim AS shift_id,
                d.KurzBez AS shift_code,
                d.Bezeichnung AS shift_name,
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

    def _map_rows(self, rows: Sequence[RowMapping]) -> tuple[Shift, ...]:
        rows_by_shift_id: dict[int, list[RowMapping]] = defaultdict(list)

        for row in rows:
            shift_id = int(
                required(
                    row["shift_id"],
                    field_name="shift_id",
                    context="TDienste",
                )
            )
            rows_by_shift_id[shift_id].append(row)

        shift_facts_by_id = {int(shift_fact.source_shift_id): shift_fact for shift_fact in self._facts.shift_facts}

        return tuple(
            self._map_shift(
                shift_id=shift_id,
                rows=shift_rows,
                shift_fact=shift_facts_by_id[shift_id],
            )
            for shift_id, shift_rows in sorted(rows_by_shift_id.items())
        )

    def _map_shift(
        self,
        *,
        shift_id: int,
        rows: list[RowMapping],
        shift_fact: TimeOfficeShiftFact,
    ) -> Shift:
        first_row = rows[0]
        context = f"TDienste shift_id={shift_id}"

        source_code = clean_text(
            required(
                first_row["shift_code"],
                field_name="shift_code",
                context=context,
            )
        )
        if source_code is None:
            raise ValueError(f"Empty TimeOffice shift code in {context}.")

        self._validate_expected_code(
            shift_id=shift_id,
            actual_code=source_code,
            expected_code=shift_fact.expected_code,
        )

        shift_type_id = int(
            required(
                first_row["shift_type_id"],
                field_name="shift_type_id",
                context=context,
            )
        )
        self._validate_real_work_shift(
            shift_id=shift_id,
            shift_type_id=shift_type_id,
        )

        segments = self._map_segments(rows=rows, shift_id=shift_id)
        start_at = segments[0][0]
        end_at = segments[-1][1]
        net_work_minutes = self._net_work_minutes(segments)

        return Shift(
            shift_id=shift_id,
            code=source_code,
            kind=shift_fact.kind,
            staffing_role=shift_fact.staffing_role,
            start_minute=self._minute_of_day(start_at),
            end_minute=self._minute_of_day(end_at),
            net_work_minutes=net_work_minutes,
        )

    def _map_segments(
        self,
        *,
        rows: list[RowMapping],
        shift_id: int,
    ) -> tuple[tuple[DateTime, DateTime, int], ...]:
        segments: list[tuple[DateTime, DateTime, int]] = []

        for row in rows:
            if row["segment_start"] is None and row["segment_end"] is None:
                continue

            context = f"TDiensteSollzeiten shift_id={shift_id}"

            start_at = required(
                to_datetime(row["segment_start"]),
                field_name="segment_start",
                context=context,
            )
            end_at = required(
                to_datetime(row["segment_end"]),
                field_name="segment_end",
                context=context,
            )
            minutes = to_non_negative_int(row["segment_minutes"])

            if end_at <= start_at:
                raise ValueError(
                    f"Invalid shift segment in {context}: segment_start={start_at!r} segment_end={end_at!r}."
                )

            segments.append((start_at, end_at, minutes))

        if not segments:
            raise ValueError(f"No timing segments found for TimeOffice shift_id={shift_id}.")

        return tuple(segments)

    def _net_work_minutes(
        self,
        segments: tuple[tuple[DateTime, DateTime, int], ...],
    ) -> int:
        source_minutes = sum(segment_minutes for _, _, segment_minutes in segments)
        if source_minutes > 0:
            return source_minutes

        return sum(int((end_at - start_at).total_seconds() // 60) for start_at, end_at, _ in segments)

    def _validate_expected_code(
        self,
        *,
        shift_id: int,
        actual_code: str,
        expected_code: str,
    ) -> None:
        if normalize_code(actual_code) != normalize_code(expected_code):
            raise ValueError(
                "Unexpected TimeOffice shift code for known scheduling shift: "
                f"shift_id={shift_id} expected={expected_code!r} actual={actual_code!r}."
            )

    def _validate_real_work_shift(
        self,
        *,
        shift_id: int,
        shift_type_id: int,
    ) -> None:
        real_work_shift_type_ids = {int(shift_type_id) for shift_type_id in self._facts.real_work_shift_type_ids}

        if shift_type_id not in real_work_shift_type_ids:
            raise ValueError(
                "Known scheduling shift is not configured as real work shift in TimeOffice: "
                f"shift_id={shift_id} shift_type_id={shift_type_id}."
            )

    def _validate_requested_shifts(
        self,
        *,
        requested_shift_ids: tuple[int, ...],
        shifts: tuple[Shift, ...],
    ) -> None:
        returned_shift_ids = {shift.shift_id for shift in shifts}
        missing_shift_ids = sorted(set(requested_shift_ids) - returned_shift_ids)

        if missing_shift_ids:
            raise ValueError(f"Missing TimeOffice shift definitions for shift_ids={missing_shift_ids}.")

    def _minute_of_day(self, value: DateTime) -> int:
        return value.hour * 60 + value.minute
