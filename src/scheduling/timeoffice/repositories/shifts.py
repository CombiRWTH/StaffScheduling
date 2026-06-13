from collections import defaultdict
from collections.abc import Sequence
from datetime import datetime as DateTime
from itertools import pairwise
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection

from src.scheduling.models.shift import Shift, ShiftKind
from src.scheduling.timeoffice.config import TimeOfficeConfig, TimeOfficeShiftConfig
from src.scheduling.timeoffice.repositories.helpers import (
    clean_text,
    minute_of_day,
    normalize_code,
    required_text,
    to_datetime,
    to_non_negative_int,
)


class TimeOfficeShiftSegment(BaseModel):
    """One TimeOffice timing segment for a shift."""

    start: DateTime
    end: DateTime
    minutes: int = Field(ge=0)


class TimeOfficeShiftSource(BaseModel):
    """Source data for one configured TimeOffice shift."""

    source_shift_id: int = Field(gt=0)
    source_code: str
    name: str

    source_shift_type_id: int
    source_statistics_group_id: int | None = None
    source_facility_id: int | None = None

    ppug_relevant: bool = False
    ppprl_relevant: bool = False
    ppug_pause_counts: bool = False

    segments: tuple[TimeOfficeShiftSegment, ...]

    start_minute: int = Field(ge=0, lt=24 * 60)
    end_minute: int = Field(ge=0, lt=24 * 60)
    ends_next_day: bool = False
    break_minutes: int = Field(default=0, ge=0)
    net_work_minutes: int = Field(ge=0)


class ShiftRepositoryResult(BaseModel):
    """Canonical output of reading TimeOffice shifts."""

    shifts: tuple[Shift, ...]


class TimeOfficeShiftRepository:
    """Read configured TimeOffice shift definitions."""

    def __init__(self, config: TimeOfficeConfig):
        self._config = config

    def fetch(self, connection: Connection) -> ShiftRepositoryResult:
        """Read configured solver-relevant shifts from TimeOffice."""
        source_shift_ids = self._config.solver_shift_ids

        if not source_shift_ids:
            raise ValueError("At least one TimeOffice solver shift id is required.")

        query = text(
            """
            SELECT
                d.Prim AS source_shift_id,
                d.KurzBez AS source_code,
                d.Bezeichnung AS name,

                d.RefDienstTypen AS source_shift_type_id,
                d.RefDiensteStatistikGruppen AS source_statistics_group_id,
                d.RefEinrichtungen AS source_facility_id,

                d.PpugRelevant AS ppug_relevant,
                d.PpprlRelevant AS ppprl_relevant,
                d.PpugPauseAnrechnen AS ppug_pause_counts,

                sz.Kommt AS segment_start,
                sz.Geht AS segment_end,
                sz.Minuten AS segment_minutes
            FROM TDienste d
            LEFT JOIN TDiensteSollzeiten sz
                ON sz.RefDienste = d.Prim
            WHERE d.Prim IN :source_shift_ids
            ORDER BY
                d.Prim,
                sz.Kommt,
                sz.Geht
            """
        ).bindparams(bindparam("source_shift_ids", expanding=True))

        rows = (
            connection.execute(
                query,
                {
                    "source_shift_ids": source_shift_ids,
                },
            )
            .mappings()
            .all()
        )

        sources = self._map_rows(rows)

        self._ensure_all_configured_shifts_found(sources)
        self._warn_about_unexpected_codes(sources)
        self._warn_about_unexpected_shift_types(sources)

        shifts = tuple(self._map_shift(source) for source in sources)

        print(f"[timeoffice] database.repository.shifts rows={len(shifts)}")

        return ShiftRepositoryResult(shifts=shifts)

    def _map_rows(self, rows: Sequence[Any]) -> tuple[TimeOfficeShiftSource, ...]:
        """Map flat SQL rows into one source object per TimeOffice shift."""
        rows_by_shift_id: dict[int, list[Any]] = defaultdict(list)

        for row in rows:
            rows_by_shift_id[row["source_shift_id"]].append(row)

        return tuple(self._map_shift_source(shift_rows) for _, shift_rows in sorted(rows_by_shift_id.items()))

    def _map_shift_source(self, rows: list[Any]) -> TimeOfficeShiftSource:
        """Map all rows for one TimeOffice shift."""
        first_row = rows[0]

        segments = tuple(segment for segment in (self._map_segment(row) for row in rows) if segment is not None)

        if not segments:
            raise ValueError(
                "Configured TimeOffice shift has no timing segments: "
                f"{first_row['source_shift_id']} / {first_row['source_code']}"
            )

        ordered_segments = tuple(sorted(segments, key=lambda segment: segment.start))

        first_segment = ordered_segments[0]
        last_segment = ordered_segments[-1]

        start_minute = minute_of_day(first_segment.start)
        end_minute = minute_of_day(last_segment.end)
        ends_next_day = last_segment.end.date() > first_segment.start.date()

        net_work_minutes = sum(segment.minutes for segment in ordered_segments)
        break_minutes = self._break_minutes(ordered_segments)

        if net_work_minutes <= 0:
            net_work_minutes = self._fallback_net_work_minutes(
                start=first_segment.start,
                end=last_segment.end,
                break_minutes=break_minutes,
            )

        return TimeOfficeShiftSource(
            source_shift_id=first_row["source_shift_id"],
            source_code=required_text(
                first_row["source_code"],
                field_name="source_code",
                context=f"shift {first_row['source_shift_id']}",
            ),
            name=self._name(
                name=first_row["name"],
                code=first_row["source_code"],
                source_shift_id=first_row["source_shift_id"],
            ),
            source_shift_type_id=first_row["source_shift_type_id"],
            source_statistics_group_id=first_row["source_statistics_group_id"],
            source_facility_id=first_row["source_facility_id"],
            ppug_relevant=bool(first_row["ppug_relevant"]),
            ppprl_relevant=bool(first_row["ppprl_relevant"]),
            ppug_pause_counts=bool(first_row["ppug_pause_counts"]),
            segments=ordered_segments,
            start_minute=start_minute,
            end_minute=end_minute,
            ends_next_day=ends_next_day,
            break_minutes=break_minutes,
            net_work_minutes=net_work_minutes,
        )

    def _map_segment(self, row: Any) -> TimeOfficeShiftSegment | None:
        """Map one TDiensteSollzeiten row to a segment."""
        if row["segment_start"] is None or row["segment_end"] is None:
            return None

        start = to_datetime(row["segment_start"])
        end = to_datetime(row["segment_end"])
        minutes = to_non_negative_int(row["segment_minutes"])

        if minutes <= 0:
            minutes = self._duration_minutes(start, end)

        return TimeOfficeShiftSegment(
            start=start,
            end=end,
            minutes=minutes,
        )

    def _map_shift(self, source: TimeOfficeShiftSource) -> Shift:
        """Map a TimeOffice shift source to a canonical solver-facing Shift."""
        configured_shift = self._configured_shift(source.source_shift_id)

        return Shift(
            shift_id=f"timeoffice:{source.source_shift_id}",
            shift_group_id=configured_shift.group_id,
            name=source.name,
            source_shift_id=source.source_shift_id,
            source_code=normalize_code(source.source_code),
            kind=configured_shift.kind,
            start_minute=source.start_minute,
            end_minute=source.end_minute,
            ends_next_day=source.ends_next_day,
            break_minutes=source.break_minutes,
            net_work_minutes=source.net_work_minutes,
            assignable=self._is_assignable(source, configured_shift),
            counts_as_work=configured_shift.counts_as_work and source.net_work_minutes > 0,
            counts_for_minimum_staffing=configured_shift.counts_for_minimum_staffing,
            is_night=configured_shift.kind == ShiftKind.NIGHT,
        )

    def _configured_shift(self, source_shift_id: int) -> TimeOfficeShiftConfig:
        """Return configured solver semantics for a TimeOffice shift id."""
        try:
            return self._config.shifts_by_id[source_shift_id]
        except KeyError as error:
            raise KeyError(f"No TimeOffice shift configuration found for source id {source_shift_id}.") from error

    def _is_assignable(
        self,
        source: TimeOfficeShiftSource,
        configured_shift: TimeOfficeShiftConfig,
    ) -> bool:
        """Return whether the solver may create decision variables for this shift."""
        if not configured_shift.assignable:
            return False

        if source.net_work_minutes <= 0:
            return False

        return source.source_shift_type_id in self._config.assignable_shift_type_ids

    def _break_minutes(self, segments: tuple[TimeOfficeShiftSegment, ...]) -> int:
        """Compute break minutes as gaps between ordered work segments."""
        break_minutes = 0

        for previous, current in pairwise(segments):
            gap = self._duration_minutes(previous.end, current.start)

            if gap > 0:
                break_minutes += gap

        return break_minutes

    def _fallback_net_work_minutes(
        self,
        start: DateTime,
        end: DateTime,
        break_minutes: int,
    ) -> int:
        """Fallback net minutes if TDiensteSollzeiten.Minuten is unavailable."""
        return max(0, self._duration_minutes(start, end) - break_minutes)

    def _duration_minutes(self, start: DateTime, end: DateTime) -> int:
        """Return duration in minutes."""
        duration = int((end - start).total_seconds() // 60)

        if duration < 0:
            raise ValueError(f"Negative TimeOffice segment duration: {start!r} -> {end!r}")

        return duration

    def _ensure_all_configured_shifts_found(self, sources: tuple[TimeOfficeShiftSource, ...]) -> None:
        """Ensure configured shift ids exist in TimeOffice."""
        found_ids = {source.source_shift_id for source in sources}
        missing_ids = sorted(set(self._config.solver_shift_ids) - found_ids)

        if missing_ids:
            raise ValueError(f"Configured TimeOffice shift ids were not found: {missing_ids}")

    def _warn_about_unexpected_codes(self, sources: tuple[TimeOfficeShiftSource, ...]) -> None:
        """Print a warning if TimeOffice code differs from configured expectation."""
        mismatches: list[str] = []

        for source in sources:
            configured_shift = self._configured_shift(source.source_shift_id)
            actual_code = normalize_code(source.source_code)
            expected_code = normalize_code(configured_shift.expected_code)

            if actual_code != expected_code:
                mismatches.append(f"{source.source_shift_id}: expected={expected_code} actual={actual_code}")

        if not mismatches:
            return

        print("[timeoffice] database.repository.shifts warning unexpected_codes=" + ", ".join(mismatches))

    def _warn_about_unexpected_shift_types(self, sources: tuple[TimeOfficeShiftSource, ...]) -> None:
        """Print a warning if a configured shift has an unexpected TimeOffice shift type."""
        unexpected: list[str] = []

        for source in sources:
            if source.source_shift_type_id not in self._config.assignable_shift_type_ids:
                unexpected.append(f"{source.source_shift_id}: type={source.source_shift_type_id}")

        if not unexpected:
            return

        print("[timeoffice] database.repository.shifts warning unexpected_shift_types=" + ", ".join(unexpected))

    def _name(self, name: Any, code: Any, source_shift_id: int) -> str:
        """Return a readable shift name."""
        cleaned_name = clean_text(name)

        if cleaned_name is not None:
            return cleaned_name

        cleaned_code = clean_text(code)

        if cleaned_code is not None:
            return cleaned_code

        return f"TimeOffice shift {source_shift_id}"
