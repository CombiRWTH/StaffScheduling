"""Native TimeOffice SELECTs, each returning canonical domain models.

Every function owns one source query together with its TimeOffice-specific translation
(codes, accounts, names) and the source-level checks that need that knowledge.
Cross-entity completeness rules live in the domain.
"""

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from math import isfinite
from typing import Any, cast

from sqlalchemy import BindParameter, Connection, RowMapping, bindparam, text

from app.domain import (
    Assignment,
    Availability,
    Employee,
    MonthlyWorkAccount,
    PlanningMonth,
    PlanningUnit,
    PlanningUnitMembership,
    Shift,
    ShiftOption,
    StaffLevel,
    WorkCredit,
    WorkSegment,
    dates_between,
    month_calendar,
)
from app.timeoffice.facts import TimeOfficeFacts


def read_units(connection: Connection, facts: TimeOfficeFacts) -> tuple[PlanningUnit, ...]:
    """All configured planning units with their TimeOffice short names."""
    rows = select_rows(
        connection,
        """
        SELECT pe.Prim AS planning_unit_id, pe.KurzBez AS planning_unit_code
        FROM TPlanungseinheiten pe
        WHERE pe.Prim IN :planning_unit_ids
        ORDER BY pe.Prim
        """,
        planning_unit_ids=sorted(facts.planning_unit_type_by_id),
    )
    if len({row["planning_unit_id"] for row in rows}) != len(rows):
        raise ValueError("Duplicate planning unit option rows.")
    if not set(facts.planning_unit_type_by_id) <= {row["planning_unit_id"] for row in rows}:
        raise ValueError("Configured planning units are missing.")
    units: list[PlanningUnit] = []
    for row in rows:
        name = _text(row["planning_unit_code"])
        if name is None:
            raise ValueError("Planning unit display names are missing.")
        unit_id = row["planning_unit_id"]
        units.append(
            PlanningUnit(planning_unit_id=unit_id, display_name=name, type=facts.planning_unit_type_by_id[unit_id])
        )
    return tuple(units)


def read_units_with_target_plan(
    connection: Connection, facts: TimeOfficeFacts, unit_ids: Sequence[int], month: PlanningMonth
) -> set[int]:
    """Units that have exactly one editable full-month target plan; plan IDs stay inside the adapter."""
    if not unit_ids:
        return set()
    rows = select_rows(
        connection,
        """
        SELECT pe.Prim AS planning_unit_id, p.Prim AS plan_id, p.RefPlanungseinheiten AS plan_planning_unit_id
        FROM TPlanungseinheiten pe
        JOIN TPlan p ON p.RefPlanungseinheiten = pe.Prim
        WHERE pe.Prim IN :planning_unit_ids
            AND p.RefPlanungsIntervalle = :planning_interval_id
            AND p.RefStati = :planning_status_id
            AND CONVERT(date, p.VonDat) = :start
            AND CONVERT(date, p.BisDat) = :end
        ORDER BY pe.Prim
        """,
        planning_unit_ids=list(unit_ids),
        start=month.start,
        end=month.end,
        planning_interval_id=facts.monthly_planning_interval_id,
        planning_status_id=facts.target_planning_status_id,
    )
    found = [row["planning_unit_id"] for row in rows]
    if any(row["plan_planning_unit_id"] != row["planning_unit_id"] for row in rows):
        raise ValueError("A TimeOffice target plan references a different planning unit.")
    if len(set(found)) != len(found):
        raise ValueError("Multiple TimeOffice target plans found for one planning unit.")
    return set(found)


def read_memberships(
    connection: Connection, facts: TimeOfficeFacts, unit_ids: Sequence[int], month: PlanningMonth
) -> tuple[PlanningUnitMembership, ...]:
    """Dated unit memberships overlapping the month, excluding those marked as not planned."""
    rows = select_rows(
        connection,
        """
        SELECT
            pep.RefPlanungseinheiten AS planning_unit_id,
            pep.RefPersonal AS employee_id,
            b.KurzBez AS membership_profession_code,
            pep.VonDat AS valid_from,
            pep.BisDat AS valid_until,
            CAST(ISNULL(pep.IstHeimat, 0) AS bit) AS is_home,
            CAST(ISNULL(pep.IstVonErsatz, 0) AS bit) AS is_replacement
        FROM TPlanungseinheitenPersonal pep
        LEFT JOIN TBerufe b ON b.Prim = pep.RefBerufe
        WHERE pep.RefPlanungseinheiten IN :planning_unit_ids
            AND CONVERT(date, pep.VonDat) <= :end
            AND (pep.BisDat IS NULL OR CONVERT(date, pep.BisDat) >= :start)
            AND ISNULL(pep.KeinEPlan, 0) = 0
        ORDER BY planning_unit_id, employee_id, valid_from, valid_until
        """,
        planning_unit_ids=list(unit_ids),
        start=month.start,
        end=month.end,
    )
    return tuple(
        PlanningUnitMembership(
            planning_unit_id=row["planning_unit_id"],
            employee_id=row["employee_id"],
            valid_from=row["valid_from"].date(),
            valid_until=row["valid_until"].date() if row["valid_until"] else None,
            staff_level=_staff_level(row["membership_profession_code"], facts, f"membership of {row['employee_id']}"),
            is_home=row["is_home"],
            is_replacement=row["is_replacement"],
        )
        for row in rows
    )


def read_planned_employee_ids(
    connection: Connection, facts: TimeOfficeFacts, employee_ids: Sequence[int], month: PlanningMonth
) -> set[int]:
    """Which of these employees have a planned membership in a configured unit during the month."""
    rows = select_rows(
        connection,
        """
        SELECT DISTINCT pep.RefPersonal AS employee_id
        FROM TPlanungseinheitenPersonal pep
        WHERE pep.RefPersonal IN :employee_ids
            AND pep.RefPlanungseinheiten IN :planning_unit_ids
            AND CONVERT(date, pep.VonDat) <= :end
            AND (pep.BisDat IS NULL OR CONVERT(date, pep.BisDat) >= :start)
            AND ISNULL(pep.KeinEPlan, 0) = 0
        """,
        employee_ids=list(employee_ids),
        planning_unit_ids=sorted(facts.planning_unit_type_by_id),
        start=month.start,
        end=month.end,
    )
    return {row["employee_id"] for row in rows}


def read_employees(connection: Connection, facts: TimeOfficeFacts, employee_ids: Sequence[int]) -> tuple[Employee, ...]:
    """Employee master data; every requested employee must exist and have a name."""
    rows = select_rows(
        connection,
        """
        SELECT
            per.Prim AS employee_id,
            b.KurzBez AS employee_profession_code,
            per.Vorname AS first_name,
            per.Name AS last_name
        FROM TPersonal per
        LEFT JOIN TBerufe b ON b.Prim = per.RefBerufe
        WHERE per.Prim IN :employee_ids
        ORDER BY per.Name, per.Vorname, per.Prim
        """,
        employee_ids=list(employee_ids),
    )
    if missing := sorted(set(employee_ids) - {row["employee_id"] for row in rows}):
        raise ValueError(f"Missing TimeOffice employee master rows for employee_ids={missing}.")
    employees: list[Employee] = []
    for row in rows:
        name = " ".join(part for part in (_text(row["last_name"]), _text(row["first_name"])) if part)
        if not name:
            raise ValueError(f"Missing TimeOffice employee display name for employee_id={row['employee_id']}.")
        employees.append(
            Employee(
                employee_id=row["employee_id"],
                display_name=name,
                staff_level=_staff_level(row["employee_profession_code"], facts, f"employee {row['employee_id']}"),
            )
        )
    return tuple(employees)


def read_accounts(
    connection: Connection,
    facts: TimeOfficeFacts,
    employee_ids: Sequence[int],
    month: PlanningMonth,
    absences: Sequence[Availability],
) -> tuple[MonthlyWorkAccount, ...]:
    """Monthly target hours (required), actual hours (optional) and dated absence credits, in minutes.

    `absences` are the employees' roster absences of the month from `read_absences`; credits are checked against them.
    """
    rows = select_rows(
        connection,
        """
        SELECT target.RefPersonal AS employee_id, target.Wert2 AS target_hours, actual.Wert2 AS actual_hours
        FROM TPersonalKontenJeMonat target
        LEFT JOIN TPersonalKontenJeMonat actual
            ON actual.RefPersonal = target.RefPersonal
            AND actual.Monat = target.Monat
            AND actual.RefKonten = :actual_account_id
        WHERE target.RefPersonal IN :employee_ids
            AND target.Monat = :month
            AND target.RefKonten = :target_account_id
        ORDER BY target.RefPersonal
        """,
        employee_ids=list(employee_ids),
        month=month.year * 100 + month.month,
        target_account_id=facts.monthly_target_work_account_id,
        actual_account_id=facts.monthly_actual_work_account_id,
    )
    credits = _read_absence_credits(connection, facts, employee_ids, month, absences)
    return tuple(
        MonthlyWorkAccount(
            employee_id=row["employee_id"],
            target_minutes=_minutes(row["target_hours"]),
            actual_minutes=None if row["actual_hours"] is None else _minutes(row["actual_hours"]),
            credit_details=tuple(credits.get(row["employee_id"], ())),
        )
        for row in rows
    )


def _read_absence_credits(
    connection: Connection,
    facts: TimeOfficeFacts,
    employee_ids: Sequence[int],
    month: PlanningMonth,
    absences: Sequence[Availability],
) -> dict[int, list[WorkCredit]]:
    """Dated credits from the TimeOffice daily absence-hour accounts, by employee.

    TimeOffice books a credited absence on every Monday-to-Friday date that is not a public holiday,
    and none on weekends or holidays. A credit without an absence of its code on that date, and a
    credited weekday absence without its booking, are source errors.
    """
    rows = select_rows(
        connection,
        """
        SELECT RefPersonal AS employee_id, Datum AS credit_date, RefKonten AS account_id, Wert AS credit_hours
        FROM TPersonalKontenJeTag
        WHERE RefPersonal IN :employee_ids
            AND RefKonten IN :credit_account_ids
            AND CONVERT(date, Datum) BETWEEN :start AND :end
        ORDER BY RefPersonal, Datum, RefKonten
        """,
        employee_ids=list(employee_ids),
        credit_account_ids=sorted(facts.credited_absence_code_by_account_id),
        start=month.start,
        end=month.end,
    )
    code_by_account = facts.credited_absence_code_by_account_id
    absent = {(row.employee_id, row.date, row.reason) for row in absences}
    booked = {(row["employee_id"], row["credit_date"].date(), code_by_account[row["account_id"]]) for row in rows}
    if orphan := sorted(booked - absent):
        employee_id, day, code = orphan[0]
        raise ValueError(f"TimeOffice credit for employee_id={employee_id} on {day} has no {code!r} absence.")
    booking_days = {day.date for day in month_calendar(month) if day.weekday <= 5 and not day.public_holiday}
    credited_codes = set(code_by_account.values())
    credited = {
        (employee_id, day, code) for employee_id, day, code in absent if day in booking_days and code in credited_codes
    }
    if unbooked := sorted(credited - booked):
        employee_id, day, code = unbooked[0]
        raise ValueError(f"TimeOffice absence {code!r} of employee_id={employee_id} on {day} has no credit booking.")
    credits: dict[int, list[WorkCredit]] = {}
    for row in rows:
        code = code_by_account[row["account_id"]]
        credits.setdefault(row["employee_id"], []).append(
            WorkCredit(
                date=row["credit_date"].date(),
                minutes=_minutes(row["credit_hours"]),
                kind="approved_absence",
                source=f"TimeOffice {code} absence",
            )
        )
    return credits


def read_absences(
    connection: Connection, facts: TimeOfficeFacts, employee_ids: Sequence[int], start: date, end: date
) -> tuple[Availability, ...]:
    """Dated roster absences from `start` to `end` as availability; ignored codes are dropped, unknown codes fail."""
    rows = select_rows(
        connection,
        """
        SELECT
            pkg.RefPersonal AS employee_id,
            pkg.Datum AS roster_date,
            COALESCE(global_absence_d.KurzBez, absence_d.KurzBez) AS resolved_absence_code
        FROM TPlanPersonalKommtGeht pkg
        LEFT JOIN TDienste global_absence_d ON global_absence_d.Prim = pkg.RefgAbw
        LEFT JOIN TDienste absence_d ON absence_d.Prim = pkg.RefDienstAbw
        WHERE pkg.RefPersonal IN :employee_ids
            AND CONVERT(date, pkg.Datum) BETWEEN :start AND :end
            AND ISNULL(pkg.Wunschdienst, 0) = 0
            AND (pkg.RefgAbw IS NOT NULL OR pkg.RefDienstAbw IS NOT NULL)
        ORDER BY pkg.RefPersonal, pkg.Datum
        """,
        employee_ids=list(employee_ids),
        start=start,
        end=end,
    )
    absences: dict[Availability, None] = {}
    for row in rows:
        code = _text(row["resolved_absence_code"])
        day: datetime = row["roster_date"]
        if code is None:
            raise ValueError(f"Missing absence code for employee_id={row['employee_id']} on {day.date()}.")
        if code in facts.ignored_availability_absence_codes:
            continue
        if code not in facts.availability_type_by_absence_code:
            raise ValueError(f"Unmapped TimeOffice absence code {code!r} for employee_id={row['employee_id']}.")
        absence = Availability(
            employee_id=row["employee_id"],
            date=day.date(),
            availability_type=facts.availability_type_by_absence_code[code],
            reason=code,
            source="TimeOffice absence",
        )
        absences[absence] = None
    return tuple(absences)


def read_shift_options(connection: Connection, facts: TimeOfficeFacts) -> tuple[ShiftOption, ...]:
    """The reduced reference shifts with their TimeOffice short codes, in day order; types are adapter facts."""
    rows = select_rows(
        connection,
        """
        SELECT d.Prim AS shift_id, d.KurzBez AS shift_code
        FROM TDienste d
        WHERE d.Prim IN :shift_ids
        """,
        shift_ids=sorted(facts.reference_shift_type_by_id),
    )
    codes = {row["shift_id"]: _text(row["shift_code"]) for row in rows}
    shift_types = facts.reference_shift_type_by_id
    if missing := [shift_id for shift_id in shift_types if not codes.get(shift_id)]:
        raise ValueError(f"Missing TimeOffice reference shifts or codes for shift_ids={missing}.")
    # Facts list the reference shifts in day order: early, intermediate, late, night.
    return tuple(
        ShiftOption(shift_id=shift_id, code=cast(str, codes[shift_id]), type=shift_type)
        for shift_id, shift_type in shift_types.items()
    )


def read_shifts(connection: Connection, facts: TimeOfficeFacts) -> tuple[Shift, ...]:
    """The reference shifts with their work segments and paid minutes from their TimeOffice target times.

    Each `TDiensteSollzeiten` row is one work segment; the gaps between them are unpaid breaks. Times
    sit on a base date and an overnight segment ends on the following one.
    """
    rows = select_rows(
        connection,
        """
        SELECT d.Prim AS shift_id, d.KurzBez AS shift_code, sz.Kommt AS segment_start, sz.Geht AS segment_end,
            sz.Minuten AS segment_minutes
        FROM TDienste d
        LEFT JOIN TDiensteSollzeiten sz ON sz.RefDienste = d.Prim
        WHERE d.Prim IN :shift_ids
        ORDER BY d.Prim, sz.Kommt
        """,
        shift_ids=sorted(facts.reference_shift_ids),
    )
    segments_by_shift: dict[int, list[RowMapping]] = {}
    for row in rows:
        segments_by_shift.setdefault(row["shift_id"], []).append(row)
    shifts: list[Shift] = []
    # Facts list the reference shifts in day order: early, intermediate, late, night.
    for shift_id, shift_type in facts.reference_shift_type_by_id.items():
        segments = segments_by_shift.get(shift_id, [])
        code = _text(segments[0]["shift_code"]) if segments else None
        if code is None:
            raise ValueError(f"Missing TimeOffice reference shift or code for shift_id={shift_id}.")
        if any(row["segment_start"] is None or row["segment_end"] is None for row in segments):
            raise ValueError(f"Missing TimeOffice shift times for shift_id={shift_id}.")
        base = datetime.combine(segments[0]["segment_start"].date(), datetime.min.time())
        # Minuten is the paid time of a segment; a segment without it counts its full length.
        minutes = sum(
            row["segment_minutes"] or _minutes_between(row["segment_start"], row["segment_end"]) for row in segments
        )
        shifts.append(
            Shift(
                shift_id=shift_id,
                code=code,
                type=shift_type,
                segments=tuple(
                    WorkSegment(
                        start_minute=_minutes_between(base, row["segment_start"]),
                        end_minute=_minutes_between(base, row["segment_end"]),
                    )
                    for row in segments
                ),
                net_work_minutes=minutes,
            )
        )
    return tuple(shifts)


def read_context_coverage(connection: Connection, facts: TimeOfficeFacts, start: date, end: date) -> set[date]:
    """Dates from `start` to `end` that a trusted context plan of every configured station spans.

    Such a plan's worked rows are complete: inside it, a date without a duty is free.
    """
    stations = facts.station_ids
    rows = select_rows(
        connection,
        """
        SELECT p.RefPlanungseinheiten AS planning_unit_id, p.VonDat AS plan_start, p.BisDat AS plan_end
        FROM TPlan p
        WHERE p.RefPlanungseinheiten IN :station_ids
            AND p.RefStati = :context_status_id
            AND CONVERT(date, p.VonDat) <= :end
            AND CONVERT(date, p.BisDat) >= :start
        """,
        station_ids=stations,
        context_status_id=facts.trusted_context_status_id,
        start=start,
        end=end,
    )
    spanned: dict[int, set[date]] = {station: set() for station in stations}
    for row in rows:
        spanned[row["planning_unit_id"]].update(dates_between(row["plan_start"].date(), row["plan_end"].date()))
    return {day for day in dates_between(start, end) if all(day in days for days in spanned.values())}


def read_context_duties(
    connection: Connection,
    facts: TimeOfficeFacts,
    employee_ids: Sequence[int],
    start: date,
    end: date,
    shifts: Sequence[Shift],
) -> tuple[Assignment, ...]:
    """Worked duties from `start` to `end` in the trusted context plans of the configured stations.

    TimeOffice stores one roster row per work segment; together they must reproduce the shift's
    catalog segments on that date, so a drifted or hand-edited duty fails instead of being guessed.
    """
    rows = select_rows(
        connection,
        """
        SELECT
            pkg.RefPersonal AS employee_id,
            pkg.Datum AS duty_date,
            pkg.RefPlanungseinheiten AS planning_unit_id,
            pkg.RefDienste AS shift_id,
            b.KurzBez AS profession_code,
            pkg.VonZeit AS segment_start,
            pkg.BisZeit AS segment_end
        FROM TPlanPersonalKommtGeht pkg
        JOIN TPlan p ON p.Prim = pkg.RefPlan
        LEFT JOIN TBerufe b ON b.Prim = pkg.RefBerufe
        WHERE pkg.RefPersonal IN :employee_ids
            AND p.RefPlanungseinheiten IN :station_ids
            AND p.RefStati = :context_status_id
            AND CONVERT(date, pkg.Datum) BETWEEN :start AND :end
            AND ISNULL(pkg.Wunschdienst, 0) = 0
            AND pkg.RefgAbw IS NULL
            AND pkg.RefDienstAbw IS NULL
        ORDER BY pkg.RefPersonal, pkg.Datum, pkg.lfdNr
        """,
        employee_ids=list(employee_ids),
        station_ids=facts.station_ids,
        context_status_id=facts.trusted_context_status_id,
        start=start,
        end=end,
    )
    by_duty: dict[tuple[int, date], list[RowMapping]] = {}
    for row in rows:
        by_duty.setdefault((row["employee_id"], row["duty_date"].date()), []).append(row)
    catalog = {shift.shift_id: shift for shift in shifts}
    duties: list[Assignment] = []
    for (employee_id, day), segments in by_duty.items():
        where = f"context duty of employee_id={employee_id} on {day}"
        first = segments[0]
        if len({(row["shift_id"], row["planning_unit_id"]) for row in segments}) > 1:
            raise ValueError(f"The {where} mixes shifts or stations.")
        shift = catalog.get(first["shift_id"])
        midnight = datetime.combine(day, datetime.min.time())
        times = [
            WorkSegment(
                start_minute=_minutes_between(midnight, row["segment_start"]),
                end_minute=_minutes_between(midnight, row["segment_end"]),
            )
            for row in segments
        ]
        if shift is None or tuple(times) != shift.segments:
            raise ValueError(f"The {where} does not match a reference shift's segments.")
        duties.append(
            Assignment(
                employee_id=employee_id,
                date=day,
                planning_unit_id=first["planning_unit_id"],
                shift_id=shift.shift_id,
                staff_level=_staff_level(first["profession_code"], facts, where),
            )
        )
    return tuple(duties)


def select_rows(connection: Connection, sql: str, **params: Any) -> Sequence[RowMapping]:
    """Run one SELECT; list parameters expand into IN clauses. An empty IN list reads nothing."""
    lists = [name for name, value in params.items() if isinstance(value, list)]
    if any(not params[name] for name in lists):
        return []
    binds: list[BindParameter[Any]] = [bindparam(name, expanding=True) for name in lists]
    query = text(sql).bindparams(*binds)
    return connection.execute(query, params).mappings().all()


def _text(value: Any) -> str | None:
    """TimeOffice stores blanks and padded codes; treat whitespace-only text as missing."""
    return str(value).strip() or None if value is not None else None


def _staff_level(profession_code: Any, facts: TimeOfficeFacts, context: str) -> StaffLevel:
    code = _text(profession_code)
    if code is None or code not in facts.staff_level_by_profession_code:
        raise ValueError(f"No qualification mapping for TimeOffice profession {code!r} ({context}).")
    return facts.staff_level_by_profession_code[code]


def _minutes_between(start: datetime, end: datetime) -> int:
    return round((end - start) / timedelta(minutes=1))


def _minutes(hours: Any) -> int:
    if hours is None or not isfinite(hours) or hours < 0:
        raise ValueError("Missing or invalid TimeOffice account hours.")
    return round(hours * 60)
