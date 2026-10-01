"""Fictional SQL boundary substitute shared by API and browser checks."""

import json
from dataclasses import replace
from datetime import date, datetime
from types import MappingProxyType
from typing import Any
from unittest.mock import MagicMock

from sqlalchemy import Engine

from app.domain import PlanningUnitType
from app.timeoffice.facts import TIMEOFFICE_FACTS
from app.timeoffice.reading.container import TimeOfficeReaders
from app.timeoffice.service import TimeOfficeService
from app.timeoffice.writing.solution import TimeOfficeSolutionWriter


class InspectionSource:
    """Run production readers/mappers over controlled query results, without SQL Server."""

    def __init__(self) -> None:
        self.missing_evidence = False
        self.missing_account = False
        self.missing_employee = False
        self.duplicate_account = False
        self.duplicate_plan = False
        self.name = "Example MFA One"
        self.queries: list[str] = []
        self.facts = replace(
            TIMEOFFICE_FACTS,
            planning_unit_type_by_id=MappingProxyType(
                {
                    101: PlanningUnitType.STATION,
                    102: PlanningUnitType.STATION,
                    201: PlanningUnitType.SHARED_POOL,
                }
            ),
        )
        engine = MagicMock(spec=Engine)
        connection = engine.connect.return_value.__enter__.return_value
        connection.execute.side_effect = self.execute
        self.connection = connection
        self.service = TimeOfficeService(
            facts=self.facts,
            engine=engine,
            readers=TimeOfficeReaders.create(facts=self.facts),
            solution_writer=TimeOfficeSolutionWriter(),
        )

    def execute(self, query: Any, params: dict[str, Any]) -> MagicMock:
        sql = str(query)
        self.queries.append(sql)
        rows: list[dict[str, Any]] = []
        if "FROM TPlanungseinheiten pe" in sql:
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
                        (201, "Example Shared Pool"),
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
                if unit in params["planning_unit_ids"] and params["start"].month != 3:
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
                (3, "Example Pool Three", "81301-010"),
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
        elif "FROM dbo.StaffSchedulingEmployeeMonthEvidence" in sql:
            day: date = params["planning_month"]
            rows = [
                {
                    "employee_id": employee,
                    "source": "Fictional complete monthly declaration",
                    "credit_details": json.dumps(
                        [
                            {
                                "date": day.isoformat(),
                                "minutes": 480,
                                "kind": "approved_absence",
                                "source": "Fictional approved leave",
                            }
                        ]
                        if employee == 1
                        else []
                    ),
                    "hard_restrictions": "[]",
                }
                for employee in params["employee_ids"]
                if not (self.missing_evidence and employee == 1)
            ]
        elif "FROM TPlanPersonalKommtGeht" in sql:
            if 1 in params["employee_ids"]:
                rows = [
                    {
                        "employee_id": 1,
                        "roster_date": datetime.combine(params["start"], datetime.min.time()),
                        "global_absence_shift_id": 7,
                        "resolved_absence_shift_id": 7,
                        "resolved_absence_code": "U",
                    }
                ]
        else:
            raise AssertionError(f"Unexpected read: {sql}")
        result = MagicMock()
        result.mappings.return_value.all.return_value = rows
        return result
