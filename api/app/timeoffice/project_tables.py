"""Reads and scoped writes of the project's supplemental tables in the TimeOffice database.

The tables come from `api/sql/supplemental-tables.sql`; nothing here creates them.
Each write replaces exactly one key (employee/date, or station/month) and runs inside the
caller's transaction, so it never depends on existing roster or plan rows.
"""

import json
from collections.abc import Sequence
from datetime import date

from sqlalchemy import Connection, text

from app.domain import (
    Availability,
    DemandCell,
    MonthlyDemand,
    PlanningMonth,
    Wish,
)
from app.timeoffice.queries import select_rows


def read_availability(
    connection: Connection, employee_ids: Sequence[int], start: date, end: date
) -> tuple[Availability, ...]:
    """Project availability of the employees from `start` to `end`."""
    rows = select_rows(
        connection,
        """
        SELECT employee_id, availability_date, availability_type, shift_ids, reason
        FROM dbo.StaffSchedulingAvailability
        WHERE employee_id IN :employee_ids AND availability_date BETWEEN :start AND :end
        ORDER BY employee_id, availability_date
        """,
        employee_ids=list(employee_ids),
        start=start,
        end=end,
    )
    return tuple(
        Availability(
            employee_id=row["employee_id"],
            date=row["availability_date"],
            availability_type=row["availability_type"],
            shift_ids=None if row["shift_ids"] is None else tuple(json.loads(row["shift_ids"])),
            reason=row["reason"],
        )
        for row in rows
    )


def insert_availability(connection: Connection, availability: Availability) -> None:
    connection.execute(
        text(
            """
            INSERT INTO dbo.StaffSchedulingAvailability
                (employee_id, availability_date, availability_type, shift_ids, reason)
            VALUES (:employee_id, :day, :availability_type, :shift_ids, :reason)
            """
        ),
        {
            "employee_id": availability.employee_id,
            "day": availability.date,
            "availability_type": availability.availability_type.value,
            "shift_ids": None if availability.shift_ids is None else json.dumps(list(availability.shift_ids)),
            "reason": availability.reason,
        },
    )


def delete_availability(connection: Connection, employee_id: int, day: date) -> None:
    connection.execute(
        text(
            "DELETE FROM dbo.StaffSchedulingAvailability WHERE employee_id = :employee_id AND availability_date = :day"
        ),
        {"employee_id": employee_id, "day": day},
    )


def read_wishes(connection: Connection, employee_ids: Sequence[int], month: PlanningMonth) -> tuple[Wish, ...]:
    rows = select_rows(
        connection,
        """
        SELECT employee_id, wish_date, wish_type, shift_id
        FROM dbo.StaffSchedulingWish
        WHERE employee_id IN :employee_ids AND wish_date BETWEEN :start AND :end
        ORDER BY employee_id, wish_date
        """,
        employee_ids=list(employee_ids),
        start=month.start,
        end=month.end,
    )
    return tuple(
        Wish(employee_id=row["employee_id"], date=row["wish_date"], type=row["wish_type"], shift_id=row["shift_id"])
        for row in rows
    )


def insert_wish(connection: Connection, wish: Wish) -> None:
    connection.execute(
        text(
            """
            INSERT INTO dbo.StaffSchedulingWish (employee_id, wish_date, wish_type, shift_id)
            VALUES (:employee_id, :day, :wish_type, :shift_id)
            """
        ),
        {"employee_id": wish.employee_id, "day": wish.date, "wish_type": wish.type.value, "shift_id": wish.shift_id},
    )


def delete_wish(connection: Connection, employee_id: int, day: date) -> None:
    connection.execute(
        text("DELETE FROM dbo.StaffSchedulingWish WHERE employee_id = :employee_id AND wish_date = :day"),
        {"employee_id": employee_id, "day": day},
    )


def read_demand(connection: Connection, planning_unit_id: int, month: PlanningMonth) -> MonthlyDemand | None:
    """The saved demand of one station month, or None when the month was never saved."""
    saved = select_rows(
        connection,
        """
        SELECT planning_unit_id FROM dbo.StaffSchedulingDemandMonth
        WHERE planning_unit_id = :planning_unit_id AND planning_month = :planning_month
        """,
        planning_unit_id=planning_unit_id,
        planning_month=month.start,
    )
    if not saved:
        return None
    rows = select_rows(
        connection,
        """
        SELECT demand_date, shift_id, staff_level, required_count
        FROM dbo.StaffSchedulingDemand
        WHERE planning_unit_id = :planning_unit_id AND demand_date BETWEEN :start AND :end
        ORDER BY demand_date, shift_id, staff_level
        """,
        planning_unit_id=planning_unit_id,
        start=month.start,
        end=month.end,
    )
    return MonthlyDemand(
        planning_unit_id=planning_unit_id,
        planning_month=month,
        cells=tuple(
            DemandCell(
                date=row["demand_date"],
                shift_id=row["shift_id"],
                staff_level=row["staff_level"],
                required_count=row["required_count"],
            )
            for row in rows
        ),
    )


def replace_demand(connection: Connection, demand: MonthlyDemand) -> None:
    """Replace one station month; other months and stations stay untouched."""
    month = demand.planning_month
    scope = {"planning_unit_id": demand.planning_unit_id}
    connection.execute(
        text(
            """
            DELETE FROM dbo.StaffSchedulingDemand
            WHERE planning_unit_id = :planning_unit_id AND demand_date BETWEEN :start AND :end
            """
        ),
        {**scope, "start": month.start, "end": month.end},
    )
    connection.execute(
        text(
            """
            DELETE FROM dbo.StaffSchedulingDemandMonth
            WHERE planning_unit_id = :planning_unit_id AND planning_month = :planning_month
            """
        ),
        {**scope, "planning_month": month.start},
    )
    connection.execute(
        text(
            """
            INSERT INTO dbo.StaffSchedulingDemandMonth (planning_unit_id, planning_month)
            VALUES (:planning_unit_id, :planning_month)
            """
        ),
        {**scope, "planning_month": month.start},
    )
    if demand.cells:
        connection.execute(
            text(
                """
                INSERT INTO dbo.StaffSchedulingDemand
                    (planning_unit_id, demand_date, shift_id, staff_level, required_count)
                VALUES (:planning_unit_id, :demand_date, :shift_id, :staff_level, :required_count)
                """
            ),
            [
                {
                    **scope,
                    "demand_date": cell.date,
                    "shift_id": cell.shift_id,
                    "staff_level": cell.staff_level.value,
                    "required_count": cell.required_count,
                }
                for cell in demand.cells
            ],
        )
