"""Published duties in the stations' TimeOffice target plans: validated rows, read-back, replacement and clear.

TimeOffice stores a duty as one `TPlanPersonalKommtGeht` row per work segment of its shift, dated on the
duty's start date and keyed by (RefPersonal, Datum, RefStati, lfdNr) without the plan. The published output
of a target plan is its worked rows marked with `Info` = `generated_duty_info`; absences, wishes, duties
entered in TimeOffice and every row of other plans are kept.

Representative write: a duty gets its reference shift's catalog segments with their wall-clock minutes,
the profession of the employee's membership at the station that books its qualification, and the
station as unit and owner, also for jumper-pool staff. Its rows are numbered after the employee's kept
rows of that date, so a native wish keeps its number.
"""

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import Connection, RowMapping, text

from app.domain import (
    Assignment,
    InvalidSelection,
    PlanningMonth,
    PublicationProblem,
    PublicationRejected,
    Shift,
)
from app.timeoffice.facts import TimeOfficeFacts
from app.timeoffice.queries import duties_from_segments, select_rows, staff_level, statement


def duty_rows(
    connection: Connection,
    facts: TimeOfficeFacts,
    plans: dict[int, int],
    shifts: Sequence[Shift],
    month: PlanningMonth,
    assignments: Sequence[Assignment],
) -> list[dict[str, Any]]:
    """The roster rows of `assignments` in the target `plans` (plan ID by station), validated against the source.

    Raises InvalidSelection for duties outside the stations, month or reference shifts or a second duty of
    an employee on one date; ValueError when no single membership profession books a duty's qualification;
    PublicationRejected (conflict) when the employee has an absence or a duty outside the replaced output that day,
    including a duty entered in TimeOffice in the target plan itself.
    """
    catalog = {shift.shift_id: shift for shift in shifts}
    if any(duty.planning_unit_id not in plans or duty.date not in month for duty in assignments):
        raise InvalidSelection("Every duty must belong to the named stations and the planning month.")
    if any(duty.shift_id not in catalog for duty in assignments):
        raise InvalidSelection("Every duty must use a reference shift.")
    if len({(duty.employee_id, duty.date) for duty in assignments}) != len(assignments):
        raise InvalidSelection("An employee can have only one duty per date.")

    employee_ids = sorted({duty.employee_id for duty in assignments})
    professions = _membership_professions(connection, employee_ids, sorted(plans), month)
    kept = _kept_rows(connection, facts, employee_ids, list(plans.values()), month)
    rows: list[dict[str, Any]] = []
    for duty in assignments:
        where = f"employee_id={duty.employee_id} on {duty.date}"
        kept_that_day = kept.get((duty.employee_id, duty.date), ())
        if any(not entry["is_wish"] for entry in kept_that_day):
            raise PublicationRejected(
                PublicationProblem.CONFLICT,
                f"TimeOffice already has an absence or another duty of {where}; generate the schedule again.",
            )
        numbered = [entry["number"] for entry in kept_that_day if entry["status_id"] == facts.target_planning_status_id]
        profession_id = _profession_id(professions, duty, facts, where)
        shift = catalog[duty.shift_id]
        midnight = datetime.combine(duty.date, datetime.min.time())
        segments = [
            (midnight + timedelta(minutes=s.start_minute), s.end_minute - s.start_minute) for s in shift.segments
        ]
        if sum(minutes for _, minutes in segments) != shift.net_work_minutes:
            raise ValueError(f"The paid minutes of shift_id={shift.shift_id} differ from its segments.")
        for number, (start, minutes) in enumerate(segments, start=max(numbered, default=0) + 1):
            rows.append(
                {
                    "plan_id": plans[duty.planning_unit_id],
                    "employee_id": duty.employee_id,
                    "roster_date": midnight,
                    "status_id": facts.target_planning_status_id,
                    "number": number,
                    "shift_id": shift.shift_id,
                    "profession_id": profession_id,
                    "planning_unit_id": duty.planning_unit_id,
                    "segment_start": start,
                    "segment_end": start + timedelta(minutes=minutes),
                    "minutes": minutes,
                    "info": facts.generated_duty_info,
                }
            )
    return rows


def insert_rows(connection: Connection, rows: list[dict[str, Any]]) -> None:
    connection.execute(
        text(
            """
            INSERT INTO TPlanPersonalKommtGeht
                (RefPlan, RefPersonal, Datum, RefStati, lfdNr, RefDienste, RefBerufe, RefPlanungseinheiten,
                VonZeit, BisZeit, Minuten, Wunschdienst, RefPeinheitOwner, Info)
            VALUES (:plan_id, :employee_id, :roster_date, :status_id, :number, :shift_id, :profession_id,
                :planning_unit_id, :segment_start, :segment_end, :minutes, 0, :planning_unit_id, :info)
            """
        ),
        rows,
    )


def read_output(
    connection: Connection, facts: TimeOfficeFacts, plan_ids: list[int], shifts: Sequence[Shift]
) -> tuple[Assignment, ...]:
    """The published duties of the target plans; rows that do not form a reference duty fail."""
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
        LEFT JOIN TBerufe b ON b.Prim = pkg.RefBerufe
        WHERE pkg.RefPlan IN :plan_ids
            AND ISNULL(pkg.Wunschdienst, 0) = 0
            AND pkg.RefgAbw IS NULL
            AND pkg.RefDienstAbw IS NULL
            AND ISNULL(pkg.Info, N'') = :generated_info
        ORDER BY pkg.RefPersonal, pkg.Datum, pkg.lfdNr
        """,
        plan_ids=plan_ids,
        generated_info=facts.generated_duty_info,
    )
    return duties_from_segments(rows, shifts, facts, "published duty")


def count_output(connection: Connection, facts: TimeOfficeFacts, plan_ids: list[int]) -> int:
    """The number of published duties (employee and date) in the target plans, whatever their rows hold."""
    rows = select_rows(
        connection,
        """
        SELECT COUNT(*) AS duties
        FROM (
            SELECT DISTINCT pkg.RefPersonal, pkg.Datum
            FROM TPlanPersonalKommtGeht pkg
            WHERE pkg.RefPlan IN :plan_ids
                AND ISNULL(pkg.Wunschdienst, 0) = 0
                AND pkg.RefgAbw IS NULL
                AND pkg.RefDienstAbw IS NULL
                AND ISNULL(pkg.Info, N'') = :generated_info
        ) published
        """,
        plan_ids=plan_ids,
        generated_info=facts.generated_duty_info,
    )
    return rows[0]["duties"]


def delete_output(connection: Connection, facts: TimeOfficeFacts, plan_ids: list[int]) -> None:
    """Delete the published duty rows of the target plans; their other rows stay."""
    params: dict[str, Any] = {"plan_ids": plan_ids, "generated_info": facts.generated_duty_info}
    connection.execute(
        statement(
            """
            DELETE pkg FROM TPlanPersonalKommtGeht pkg
            WHERE pkg.RefPlan IN :plan_ids
                AND ISNULL(pkg.Wunschdienst, 0) = 0
                AND pkg.RefgAbw IS NULL
                AND pkg.RefDienstAbw IS NULL
                AND ISNULL(pkg.Info, N'') = :generated_info
            """,
            params,
        ),
        params,
    )


def _kept_rows(
    connection: Connection, facts: TimeOfficeFacts, employee_ids: list[int], plan_ids: list[int], month: PlanningMonth
) -> dict[tuple[int, date], list[dict[str, Any]]]:
    """The employees' roster rows of the month that publication keeps, by employee and date."""
    rows = select_rows(
        connection,
        """
        SELECT
            pkg.RefPersonal AS employee_id,
            pkg.Datum AS roster_date,
            pkg.RefStati AS status_id,
            pkg.lfdNr AS number,
            CAST(ISNULL(pkg.Wunschdienst, 0) AS bit) AS is_wish
        FROM TPlanPersonalKommtGeht pkg
        WHERE pkg.RefPersonal IN :employee_ids
            AND CONVERT(date, pkg.Datum) BETWEEN :start AND :end
            AND NOT (
                pkg.RefPlan IN :plan_ids
                AND ISNULL(pkg.Wunschdienst, 0) = 0
                AND pkg.RefgAbw IS NULL
                AND pkg.RefDienstAbw IS NULL
                AND ISNULL(pkg.Info, N'') = :generated_info
            )
        """,
        employee_ids=employee_ids,
        plan_ids=plan_ids,
        generated_info=facts.generated_duty_info,
        start=month.start,
        end=month.end,
    )
    kept: dict[tuple[int, date], list[dict[str, Any]]] = {}
    for row in rows:
        kept.setdefault((row["employee_id"], row["roster_date"].date()), []).append(dict(row))
    return kept


def _membership_professions(
    connection: Connection, employee_ids: list[int], unit_ids: list[int], month: PlanningMonth
) -> Sequence[RowMapping]:
    """The employees' planned memberships at the stations overlapping the month, with their profession."""
    return select_rows(
        connection,
        """
        SELECT
            pep.RefPersonal AS employee_id,
            pep.RefPlanungseinheiten AS planning_unit_id,
            pep.RefBerufe AS profession_id,
            b.KurzBez AS profession_code,
            pep.VonDat AS valid_from,
            pep.BisDat AS valid_until
        FROM TPlanungseinheitenPersonal pep
        LEFT JOIN TBerufe b ON b.Prim = pep.RefBerufe
        WHERE pep.RefPersonal IN :employee_ids
            AND pep.RefPlanungseinheiten IN :planning_unit_ids
            AND CONVERT(date, pep.VonDat) <= :end
            AND (pep.BisDat IS NULL OR CONVERT(date, pep.BisDat) >= :start)
            AND ISNULL(pep.KeinEPlan, 0) = 0
        """,
        employee_ids=employee_ids,
        planning_unit_ids=unit_ids,
        start=month.start,
        end=month.end,
    )


def _profession_id(memberships: Sequence[RowMapping], duty: Assignment, facts: TimeOfficeFacts, where: str) -> int:
    """The one profession of the employee's active station membership that books the duty's qualification."""
    found = {
        row["profession_id"]
        for row in memberships
        if row["employee_id"] == duty.employee_id
        and row["planning_unit_id"] == duty.planning_unit_id
        and row["valid_from"].date() <= duty.date
        and (row["valid_until"] is None or duty.date <= row["valid_until"].date())
        and staff_level(row["profession_code"], facts, f"membership of {where}") == duty.staff_level
    }
    if len(found) != 1:
        raise ValueError(f"No single {duty.staff_level.value} membership profession at the station for {where}.")
    return found.pop()
