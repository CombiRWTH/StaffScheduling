from datetime import datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.reading.types import CleanText, SourceInt, SourceNullableInt, TimeOfficeSourceRow


class TimeOfficeShiftRow(TimeOfficeSourceRow):
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


class TimeOfficeShiftReader:
    """Reads TimeOffice reference-shift source rows."""

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def read_rows(self, *, connection: Connection) -> tuple[TimeOfficeShiftRow, ...]:
        shift_ids = tuple(self._facts.reference_shift_facts_by_id.keys())

        if not shift_ids:
            return ()

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

        raw_rows = connection.execute(query, {"shift_ids": shift_ids}).mappings().all()

        return tuple(TimeOfficeShiftRow.model_validate(row) for row in raw_rows)
