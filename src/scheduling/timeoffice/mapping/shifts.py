from collections import defaultdict
from datetime import datetime

from scheduling.domain import Shift
from scheduling.domain.shift import ShiftId
from scheduling.timeoffice.facts import TimeOfficeFacts, TimeOfficeReferenceShiftFact
from scheduling.timeoffice.reading.shifts import TimeOfficeShiftRow


def map_shifts(rows: tuple[TimeOfficeShiftRow, ...], *, facts: TimeOfficeFacts) -> tuple[Shift, ...]:
    rows_by_shift_id = _group_shift_rows(rows)
    _fail_if_reference_shifts_are_missing(rows_by_shift_id=rows_by_shift_id, facts=facts)
    _fail_if_unexpected_shift_rows_exist(rows_by_shift_id=rows_by_shift_id, facts=facts)

    return tuple(
        _map_reference_shift(
            shift_id=shift_id,
            rows=shift_rows,
            shift_fact=_require_reference_shift_fact(shift_id=shift_id, facts=facts),
            facts=facts,
        )
        for shift_id, shift_rows in sorted(rows_by_shift_id.items())
    )


def reference_shift_id_for_source_shift(
    *,
    source_shift_id: int | None,
    source_shift_code: str | None,
    facts: TimeOfficeFacts,
    context: str,
) -> ShiftId:
    if source_shift_id is None:
        raise ValueError(f"Missing TimeOffice source shift ID for {context}: source_shift_code={source_shift_code!r}.")

    reference_fact = facts.reference_shift_facts_by_id.get(source_shift_id)
    if reference_fact is not None:
        _check_reference_shift_code(
            source_shift_id=source_shift_id,
            source_shift_code=source_shift_code,
            expected_code=reference_fact.expected_code,
            context=context,
        )
        return source_shift_id

    override_shift_id = facts.shift_id_overrides.get(source_shift_id)
    if override_shift_id is not None:
        if override_shift_id not in facts.reference_shift_facts_by_id:
            raise ValueError(
                f"TimeOffice shift override points to non-reference shift for {context}: "
                f"source_shift_id={source_shift_id} "
                f"source_shift_code={source_shift_code!r} "
                f"override_shift_id={override_shift_id}."
            )

        return override_shift_id

    known_reference_ids = sorted(facts.reference_shift_facts_by_id)
    known_override_ids = sorted(facts.shift_id_overrides)

    raise ValueError(
        f"Unmapped TimeOffice source shift for {context}: "
        f"source_shift_id={source_shift_id} "
        f"source_shift_code={source_shift_code!r}. "
        f"Known reference_shift_ids={known_reference_ids}; "
        f"known_override_shift_ids={known_override_ids}."
    )


def _map_reference_shift(
    *,
    shift_id: ShiftId,
    rows: list[TimeOfficeShiftRow],
    shift_fact: TimeOfficeReferenceShiftFact,
    facts: TimeOfficeFacts,
) -> Shift:
    first_row = rows[0]

    _check_reference_shift_code(
        source_shift_id=shift_id,
        source_shift_code=first_row.shift_code,
        expected_code=shift_fact.expected_code,
        context="reference shift definition",
    )

    if first_row.shift_type_id != facts.work_shift_type_id:
        raise ValueError(
            "Reference shift is not configured as normal work shift in TimeOffice: "
            f"shift_id={shift_id} "
            f"shift_code={first_row.shift_code!r} "
            f"shift_type_id={first_row.shift_type_id} "
            f"expected_work_shift_type_id={facts.work_shift_type_id}."
        )

    segments = _shift_segments(rows=rows, shift_id=shift_id)

    return Shift(
        shift_id=shift_id,
        code=first_row.shift_code,
        type=shift_fact.type,
        staffing_role=shift_fact.staffing_role,
        start_minute=_minute_of_day(segments[0][0]),
        end_minute=_minute_of_day(segments[-1][1]),
        net_work_minutes=_net_work_minutes(segments),
    )


def _check_reference_shift_code(
    *,
    source_shift_id: int,
    source_shift_code: str | None,
    expected_code: str,
    context: str,
) -> None:
    if source_shift_code is None:
        raise ValueError(
            f"Missing TimeOffice shift code for {context}: "
            f"source_shift_id={source_shift_id} "
            f"expected_code={expected_code!r}."
        )

    if source_shift_code != expected_code:
        raise ValueError(
            f"Unexpected TimeOffice shift code for {context}: "
            f"source_shift_id={source_shift_id} "
            f"expected_code={expected_code!r} "
            f"actual_code={source_shift_code!r}."
        )


def _require_reference_shift_fact(*, shift_id: ShiftId, facts: TimeOfficeFacts) -> TimeOfficeReferenceShiftFact:
    shift_fact = facts.reference_shift_facts_by_id.get(shift_id)

    if shift_fact is None:
        raise ValueError(f"Unknown reference shift_id: shift_id={shift_id}.")

    return shift_fact


def _group_shift_rows(rows: tuple[TimeOfficeShiftRow, ...]) -> dict[ShiftId, list[TimeOfficeShiftRow]]:
    rows_by_shift_id: dict[ShiftId, list[TimeOfficeShiftRow]] = defaultdict(list)

    for row in rows:
        rows_by_shift_id[row.shift_id].append(row)

    return dict(rows_by_shift_id)


def _fail_if_reference_shifts_are_missing(
    *, rows_by_shift_id: dict[ShiftId, list[TimeOfficeShiftRow]], facts: TimeOfficeFacts
) -> None:
    missing_shift_ids = sorted(set(facts.reference_shift_facts_by_id) - set(rows_by_shift_id))

    if missing_shift_ids:
        raise ValueError(f"Missing TimeOffice rows for reference shift_ids={missing_shift_ids}.")


def _fail_if_unexpected_shift_rows_exist(
    *, rows_by_shift_id: dict[ShiftId, list[TimeOfficeShiftRow]], facts: TimeOfficeFacts
) -> None:
    unexpected_shift_ids = sorted(set(rows_by_shift_id) - set(facts.reference_shift_facts_by_id))

    if unexpected_shift_ids:
        raise ValueError(f"TimeOffice returned unexpected shift rows for shift_ids={unexpected_shift_ids}.")


def _shift_segments(*, rows: list[TimeOfficeShiftRow], shift_id: ShiftId) -> tuple[tuple[datetime, datetime, int], ...]:
    segments = tuple(
        (
            row.segment_start,
            row.segment_end,
            row.segment_minutes or 0,
        )
        for row in rows
        if row.segment_start is not None and row.segment_end is not None
    )

    if not segments:
        raise ValueError(f"No timing segments found for reference shift_id={shift_id}.")

    return segments


def _minute_of_day(value: datetime) -> int:
    return value.hour * 60 + value.minute


def _net_work_minutes(segments: tuple[tuple[datetime, datetime, int], ...]) -> int:
    source_minutes = sum(segment_minutes for _, _, segment_minutes in segments)

    if source_minutes > 0:
        return source_minutes

    return sum(int((end_at - start_at).total_seconds() // 60) for start_at, end_at, _ in segments)
