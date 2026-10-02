"""Fictional SQL boundary substitute shared by API and browser checks."""

import copy
import re
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timedelta
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock

from sqlalchemy import Engine

from app.domain import PlanningUnitType
from app.timeoffice import TimeOfficeConflict, TimeOfficeService, TimeOfficeUnavailable
from app.timeoffice.facts import (
    GENERATED_DUTY_INFO,
    SCHOOL_CREDIT_ACCOUNT_ID,
    TIMEOFFICE_FACTS,
    VACATION_CREDIT_ACCOUNT_ID,
)

SHIFT_CODES = {1113: "F", 1453: "Z", 1605: "S", 1690: "N"}

# Target-time segments of the reference shifts as in TimeOffice: (start, end, paid minutes or None).
DAY = datetime(2000, 1, 1)
SHIFT_SEGMENTS = {
    1113: [
        (DAY.replace(hour=5, minute=55), DAY.replace(hour=10), 245),
        (DAY.replace(hour=10, minute=30), DAY.replace(hour=13, minute=25), 175),
    ],
    1453: [(DAY.replace(hour=8, minute=30), DAY.replace(hour=14, minute=15), None)],
    1605: [
        (DAY.replace(hour=13, minute=15), DAY.replace(hour=16), 165),
        (DAY.replace(hour=16, minute=30), DAY.replace(hour=21), 270),
    ],
    1690: [
        (DAY.replace(hour=20, minute=10), DAY.replace(hour=21, minute=45), 95),
        (DAY.replace(hour=22), DAY.replace(day=2), 120),
        (DAY.replace(day=2, minute=30), DAY.replace(day=2, hour=6, minute=10), 340),
    ],
}

# TBerufe.Prim of the fixture's profession codes, as roster rows and memberships reference them.
PROFESSION_IDS = {"81102-004": 124, "81302-028": 651, "81301-010": 334}
PROFESSION_CODES = {prim: code for code, prim in PROFESSION_IDS.items()}

# Key columns of each project table, used to apply the adapter's scoped DELETEs.
PROJECT_TABLES = {
    "StaffSchedulingAvailability": ("employee_id", "availability_date"),
    "StaffSchedulingWish": ("employee_id", "wish_date"),
    "StaffSchedulingDemandMonth": ("planning_unit_id", "planning_month"),
    "StaffSchedulingDemand": ("planning_unit_id", "demand_date"),
}


class InspectionSource:
    """Run production readers/mappers over controlled query results, without SQL Server.

    Native TimeOffice tables return fixed fictional rows. The project tables are a small in-memory
    store with transactional `engine.begin()`, so adapter writes can be read back.
    """

    def __init__(self) -> None:
        self.orphan_credit = False
        self.unbooked_absence = False
        self.missing_account = False
        self.missing_employee = False
        self.duplicate_account = False
        self.duplicate_plan = False
        self.missing_shift_times = False
        # Context plans span the 14 days before every month; employee 2 works their last night.
        self.context_plans = True
        self.drifted_context_duty = False
        self.name = "Example MFA One"
        self.queries: list[str] = []
        self.tables: dict[str, list[dict[str, Any]]] = {name: [] for name in PROJECT_TABLES}
        # Writes naming one of these employee or station IDs fail like a lost connection.
        self.failing_ids: set[int] = set()
        # Writable TPlanPersonalKommtGeht rows (published duties, test wishes, absences, duties entered in
        # TimeOffice and other plans' duties), keyed like TimeOffice by (employee_id, roster_date, status_id,
        # number) without the plan.
        self.roster: list[dict[str, Any]] = []
        # Roster inserts naming one of these employee or station IDs collide like a concurrent writer.
        self.conflicting_ids: set[int] = set()
        # Called before roster rows are inserted, so a test can hold a publication mid-transaction.
        self.before_roster_insert: Callable[[], None] = lambda: None
        self.facts = replace(
            TIMEOFFICE_FACTS,
            planning_unit_type_by_id=MappingProxyType(
                {
                    101: PlanningUnitType.STATION,
                    102: PlanningUnitType.STATION,
                    201: PlanningUnitType.JUMPER_POOL,
                }
            ),
        )
        engine = MagicMock(spec=Engine)
        connection = engine.connect.return_value.__enter__.return_value
        connection.execute.side_effect = self.execute
        engine.begin.side_effect = self._transaction
        engine.execution_options.return_value = engine
        self.connection = connection
        self.service = TimeOfficeService(
            facts=self.facts,
            engine=engine,
        )

    @contextmanager
    def _transaction(self) -> Generator[MagicMock]:
        before = copy.deepcopy((self.tables, self.roster))
        try:
            yield self.connection
        except BaseException:
            self.tables, self.roster = before
            raise

    @staticmethod
    def is_output(row: dict[str, Any], plan_ids: list[int]) -> bool:
        """A published duty row of one of the target plans, as publication's SQL defines its output."""
        return (
            row["plan_id"] in plan_ids
            and not row.get("wish")
            and not row.get("absence")
            and row.get("info") == GENERATED_DUTY_INFO
        )

    def _write_roster(self, sql: str, params: dict[str, Any] | list[dict[str, Any]]) -> None:
        if sql.lstrip().startswith("DELETE"):
            assert isinstance(params, dict)
            self.roster = [row for row in self.roster if not self.is_output(row, params["plan_ids"])]
            return
        assert isinstance(params, list)
        self.before_roster_insert()
        for row in params:
            ids = {row["employee_id"], row["planning_unit_id"]}
            if ids & self.failing_ids:
                raise TimeOfficeUnavailable("query", "TimeOffice query failed.")
            key = (row["employee_id"], row["roster_date"], row["status_id"], row["number"])
            if ids & self.conflicting_ids or any(
                (r["employee_id"], r["roster_date"], r["status_id"], r["number"]) == key for r in self.roster
            ):
                raise TimeOfficeConflict("TimeOffice changed concurrently.")
            self.roster.append(dict(row))

    def _roster_rows(self, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        """Publication's reads of the writable roster."""
        plan_ids = params["plan_ids"]
        if "COUNT(*) AS duties" in sql:
            duties = {(r["employee_id"], r["roster_date"]) for r in self.roster if self.is_output(r, plan_ids)}
            return [{"duties": len(duties)}]
        if "AND NOT (" in sql:
            # The fixture's static approved absence of employee 1 on the 1st, then the writable rows.
            first = datetime.combine(params["start"], datetime.min.time())
            kept: list[dict[str, Any]] = [
                {"employee_id": 1, "roster_date": first, "status_id": 20, "number": 1, "is_wish": False},
                *(
                    {
                        **{k: r[k] for k in ("employee_id", "roster_date", "status_id", "number")},
                        "is_wish": bool(r.get("wish")),
                    }
                    for r in self.roster
                    if not self.is_output(r, plan_ids)
                ),
            ]
            return [
                row
                for row in kept
                if row["employee_id"] in params["employee_ids"]
                and params["start"] <= row["roster_date"].date() <= params["end"]
            ]
        output = sorted(
            (r for r in self.roster if self.is_output(r, plan_ids)),
            key=lambda r: (r["employee_id"], r["roster_date"], r["number"]),
        )
        return [
            {
                "employee_id": r["employee_id"],
                "duty_date": r["roster_date"],
                "planning_unit_id": r["planning_unit_id"],
                "shift_id": r["shift_id"],
                "profession_code": PROFESSION_CODES[r["profession_id"]],
                "segment_start": r["segment_start"],
                "segment_end": r["segment_end"],
            }
            for r in output
        ]

    def _write(self, sql: str, params: dict[str, Any] | list[dict[str, Any]]) -> None:
        if "TPlanPersonalKommtGeht" in sql:
            self._write_roster(sql, params)
            return
        first = params[0] if isinstance(params, list) else params
        if {first.get("employee_id"), first.get("planning_unit_id")} & self.failing_ids:
            raise TimeOfficeUnavailable("query", "TimeOffice query failed.")
        table = next(name for name in PROJECT_TABLES if re.search(rf"dbo\.{name}\b", sql))
        if sql.lstrip().startswith("INSERT"):
            columns = sql.split("(", 1)[1].split(")", 1)[0].replace("\n", " ").split(",")
            values = sql.split("VALUES", 1)[1].strip().strip("()").split(",")
            for row in params if isinstance(params, list) else [params]:
                self.tables[table].append(
                    {
                        column.strip(): row[value.strip().lstrip(":")]
                        for column, value in zip(columns, values, strict=True)
                    }
                )
            return
        assert isinstance(params, dict)
        key, day = PROJECT_TABLES[table]

        def hit(row: dict[str, Any]) -> bool:
            if "BETWEEN" in sql:
                return row[key] == params[key] and params["start"] <= row[day] <= params["end"]
            return row[key] == params[key] and row[day] == params.get("day", params.get(day))

        self.tables[table] = [row for row in self.tables[table] if not hit(row)]

    def _project_rows(self, table: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        key, day = PROJECT_TABLES[table]
        keys = params.get(f"{key}s", [params.get(key)])
        return [
            dict(row)
            for row in self.tables[table]
            if row[key] in keys
            and (params["start"] <= row[day] <= params["end"] if "start" in params else row[day] == params[day])
        ]

    def execute(self, query: Any, params: dict[str, Any] | list[dict[str, Any]]) -> MagicMock:
        sql = str(query)
        self.queries.append(sql)
        rows: list[dict[str, Any]] = []
        if sql.lstrip().startswith(("INSERT", "DELETE")):
            self._write(sql, params)
            return MagicMock()
        assert isinstance(params, dict)
        if "FROM dbo.StaffSchedulingDemandMonth" in sql:
            rows = self._project_rows("StaffSchedulingDemandMonth", params)
        elif "FROM dbo.StaffSchedulingDemand" in sql:
            rows = self._project_rows("StaffSchedulingDemand", params)
        elif "FROM dbo.StaffSchedulingAvailability" in sql:
            rows = self._project_rows("StaffSchedulingAvailability", params)
        elif "FROM dbo.StaffSchedulingWish" in sql:
            rows = self._project_rows("StaffSchedulingWish", params)
        elif "JOIN TDiensteSollzeiten sz" in sql:
            rows = [
                {"shift_id": shift, "shift_code": SHIFT_CODES[shift], **segment}
                for shift in params["shift_ids"]
                for segment in (
                    [{"segment_start": None, "segment_end": None, "segment_minutes": None}]
                    if self.missing_shift_times and shift == 1690
                    else [
                        {"segment_start": start, "segment_end": end, "segment_minutes": minutes}
                        for start, end, minutes in SHIFT_SEGMENTS[shift]
                    ]
                )
            ]
        elif "FROM TDienste d" in sql:
            rows = [{"shift_id": shift, "shift_code": SHIFT_CODES[shift]} for shift in params["shift_ids"]]
        elif "FROM TPlanungseinheiten pe" in sql:
            if "JOIN TPlan p" in sql:
                available = {101, 102} if params["start"].month != 2 else {102}
                rows = [
                    {"planning_unit_id": unit, "plan_id": unit + 1000, "plan_planning_unit_id": unit}
                    for unit in params["planning_unit_ids"]
                    if unit in available
                ]
                if self.duplicate_plan and rows:
                    rows.append(rows[0])
            else:
                rows = [
                    {"planning_unit_id": unit, "planning_unit_code": name}
                    for unit, name in [
                        (101, "Example Station North"),
                        (102, "Example Station South"),
                        (201, "Example Jumper Pool"),
                    ]
                ]
        elif "FROM TPlanungseinheitenPersonal" in sql:
            for employee, unit, home, replacement, code in [
                (1, 201, True, False, "81102-004"),
                (1, 101, False, True, "81102-004"),
                (1, 102, False, True, "81102-004"),
                (2, 101, True, False, "81302-028"),
                (3, 201, True, False, "81301-010"),
            ]:
                if (
                    unit in params["planning_unit_ids"]
                    and employee in params.get("employee_ids", [employee])
                    and params["start"].month != 3
                ):
                    rows.append(
                        {
                            "planning_unit_id": unit,
                            "employee_id": employee,
                            "membership_profession_code": code,
                            "profession_id": PROFESSION_IDS[code],
                            "profession_code": code,
                            "valid_from": datetime(2025, 12, 1),
                            "valid_until": datetime(2026, 6, 30),
                            "is_home": home,
                            "is_replacement": replacement,
                        }
                    )
        elif "FROM TPersonal per" in sql:
            for employee, name, code in [
                (1, self.name, "81102-004"),
                (2, "Example Team Two", "81302-028"),
                (3, "Example Jumper Three", "81301-010"),
            ]:
                if employee in params["employee_ids"] and not (self.missing_employee and employee == 1):
                    rows.append(
                        {
                            "employee_id": employee,
                            "employee_profession_id": 1,
                            "employee_profession_code": code,
                            "first_name": None,
                            "last_name": name,
                        }
                    )
        elif "FROM TPersonalKontenJeMonat target" in sql:
            # Jumper Three has no station membership, so only a zero target is reachable.
            rows = [
                {
                    "employee_id": employee,
                    "month": params["month"],
                    "target_hours": 0.0 if employee == 3 else 160.0,
                    "actual_hours": 0.0,
                }
                for employee in params["employee_ids"]
                if not (self.missing_account and employee == 1)
            ]
            if self.duplicate_account:
                rows.append(rows[0])
        elif "FROM TPersonalKontenJeTag" in sql:
            # Employee 1's vacation on the 1st is credited eight hours on the vacation account.
            first = datetime.combine(params["start"], datetime.min.time())
            rows = [
                {"employee_id": 1, "credit_date": first, "account_id": VACATION_CREDIT_ACCOUNT_ID, "credit_hours": 8.0}
            ]
            if self.orphan_credit:
                rows.append(
                    {
                        "employee_id": 2,
                        "credit_date": first,
                        "account_id": SCHOOL_CREDIT_ACCOUNT_ID,
                        "credit_hours": 7.8,
                    }
                )
            rows = [row for row in rows if row["employee_id"] in params["employee_ids"]]
        elif "FROM TPlan p" in sql and "p.RefStati = :context_status_id" in sql:
            # Each station has a trusted plan of the last 14 days of every month, like the prepared December.
            month_ends = [datetime(2026, month, 1) - timedelta(days=1) for month in range(1, 13)]
            rows = [
                {"planning_unit_id": unit, "plan_start": end - timedelta(days=13), "plan_end": end}
                for end in month_ends
                for unit in params["station_ids"]
                if self.context_plans
            ]
        elif "FROM TPlanPersonalKommtGeht" in sql and "plan_ids" in params:
            rows = self._roster_rows(sql, params)
        elif "FROM TPlanPersonalKommtGeht" in sql and "p.RefStati = :context_status_id" in sql:
            # The night of December 31, one row per catalog segment; a drifted one ends late.
            night = datetime(2025, 12, 31)
            late = timedelta(minutes=10 if self.drifted_context_duty else 0)
            segments = SHIFT_SEGMENTS[1690]
            rows = [
                {
                    "employee_id": 2,
                    "duty_date": night,
                    "planning_unit_id": 101,
                    "shift_id": 1690,
                    "profession_code": "81302-028",
                    "segment_start": night + (segment_start - DAY),
                    "segment_end": night + (segment_end - DAY) + (late if index == len(segments) - 1 else timedelta()),
                }
                for index, (segment_start, segment_end, _) in enumerate(segments)
                if self.context_plans
                and 2 in params["employee_ids"]
                and params["start"] <= night.date() <= params["end"]
            ]
        elif "FROM TPlanPersonalKommtGeht" in sql:
            first = datetime.combine(params["start"], datetime.min.time())
            roster = [
                # An approved absence: the only kind of roster row planning may use.
                {"employee_id": 1, "roster_date": first, "resolved_absence_code": "U"},
                # Without its credit booking only when `unbooked_absence`: a school day on a regular weekday.
                *(
                    [{"employee_id": 2, "roster_date": datetime(2026, 1, 2), "resolved_absence_code": "SC"}]
                    if self.unbooked_absence
                    else []
                ),
                # Polluted worked shifts: an unmapped shift in another plan and earlier output in the target.
                {"employee_id": 2, "roster_date": first, "plan_id": 9, "work_shift_id": 9999},
                {"employee_id": 1, "roster_date": first.replace(day=2), "plan_id": 1101, "work_shift_id": 1113},
            ]
            # Apply the query's own row filter, so a query that reads worked shifts would see them.
            absences_only = "pkg.RefgAbw IS NOT NULL OR pkg.RefDienstAbw IS NOT NULL" in sql
            rows = [
                row
                for row in roster
                if row["employee_id"] in params["employee_ids"] and ("work_shift_id" not in row or not absences_only)
            ]
        else:
            raise AssertionError(f"Unexpected read: {sql}")
        result = MagicMock()
        result.mappings.return_value.all.return_value = rows
        return result
