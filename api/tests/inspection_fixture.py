"""Fictional SQL boundary substitute shared by API and browser checks."""

import copy
import re
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock

from sqlalchemy import Engine

from app.domain import PlanningUnitType
from app.timeoffice import TimeOfficeService, TimeOfficeUnavailable
from app.timeoffice.facts import SCHOOL_CREDIT_ACCOUNT_ID, TIMEOFFICE_FACTS, VACATION_CREDIT_ACCOUNT_ID

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
        self.name = "Example MFA One"
        self.queries: list[str] = []
        self.tables: dict[str, list[dict[str, Any]]] = {name: [] for name in PROJECT_TABLES}
        # Writes naming one of these employee or station IDs fail like a lost connection.
        self.failing_ids: set[int] = set()
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
        self.connection = connection
        self.service = TimeOfficeService(
            facts=self.facts,
            engine=engine,
        )

    @contextmanager
    def _transaction(self) -> Generator[MagicMock]:
        before = copy.deepcopy(self.tables)
        try:
            yield self.connection
        except BaseException:
            self.tables = before
            raise

    def _write(self, sql: str, params: dict[str, Any] | list[dict[str, Any]]) -> None:
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

    def execute(self, query: Any, params: dict[str, Any]) -> MagicMock:
        sql = str(query)
        self.queries.append(sql)
        rows: list[dict[str, Any]] = []
        if sql.lstrip().startswith(("INSERT", "DELETE")):
            self._write(sql, params)
            return MagicMock()
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
                            "membership_profession_id": 1,
                            "membership_profession_code": code,
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
            rows = [
                {"employee_id": employee, "month": params["month"], "target_hours": 160.0, "actual_hours": 0.0}
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
