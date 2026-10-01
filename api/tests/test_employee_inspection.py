import json
from datetime import date
from typing import Any, cast
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from inspection_fixture import InspectionSource

from app.dependencies import get_timeoffice_service
from app.domain import PlanningMonth, StaffLevel
from app.main import app
from app.timeoffice.mapping.work_accounts import map_monthly_work_accounts
from app.timeoffice.reading.work_accounts import TimeOfficeMonthlyWorkAccountRow


def test_combined_scope_retains_identity_memberships_mfa_origin_and_account_evidence() -> None:
    source = InspectionSource()
    month = PlanningMonth(year=2026, month=1)
    result = source.service.inspect_employees(planning_unit_ids=(101, 102, 101), planning_month=month)
    assert result.selected_station_ids == (101, 102)
    assert [employee.employee_id for employee in result.employees] == [1, 2, 3]
    employee = result.employees[0]
    assert employee.staff_level == StaffLevel.MFA
    assert {row.planning_unit_id for row in employee.memberships if row.is_home} == {201}
    assert {row.planning_unit_id for row in employee.memberships if row.is_replacement} == {101, 102}
    assert len(employee.memberships) == 3
    assert employee.account.target_minutes == 9600
    assert employee.account.actual_minutes == 0
    assert employee.account.credited_minutes == 480
    assert employee.hard_restrictions[0].date == date(2026, 1, 1)
    assert employee.hard_restrictions[0].reason == "U"
    # A pool origin alone does not imply eligibility at either destination.
    assert {row.planning_unit_id for row in result.employees[2].memberships} == {201}
    source.name = "Renamed Example"
    renamed = source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=month)
    assert renamed.employees[0].employee_id == employee.employee_id
    assert renamed.employees[0].display_name == "Renamed Example"
    assert not any(word in sql.upper() for sql in source.queries for word in ("CREATE TABLE", "INSERT ", "DELETE "))
    assert not any("FROM TPlanPersonal " in sql for sql in source.queries)

    original_execute = source.execute

    def two_absence_reasons(query: Any, params: dict[str, Any]) -> MagicMock:
        result = original_execute(query, params)
        if "TPlanPersonalKommtGeht" in str(query):
            rows = result.mappings.return_value.all.return_value
            rows.append({**rows[0], "resolved_absence_code": "ZU"})
        return result

    source.connection.execute.side_effect = two_absence_reasons
    distinct = source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=month)
    assert {row.reason for row in distinct.employees[0].hard_restrictions} == {"U", "ZU"}


@pytest.mark.parametrize(
    "flag",
    ["missing_evidence", "missing_account", "missing_employee", "duplicate_account", "duplicate_plan", "missing_name"],
)
def test_missing_or_ambiguous_source_facts_fail_the_whole_inspection(flag: str) -> None:
    source = InspectionSource()
    if flag == "missing_name":
        source.name = ""
    else:
        setattr(source, flag, True)
    with pytest.raises(ValueError, match="requires|require|Missing|Multiple"):
        source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=PlanningMonth(year=2026, month=1))


def test_options_full_month_and_http_failure_contract() -> None:
    source = InspectionSource()
    app.dependency_overrides[get_timeoffice_service] = lambda: source.service
    try:
        client = cast(httpx.Client, TestClient(app))
        response = client.get("/planning/options?year=2026&month=2")
        assert response.status_code == 200
        assert [row["planning_unit_id"] for row in response.json()["planning_units"]] == [102]
        assert response.json()["planning_month"]["end"] == "2026-02-28"
        assert client.get("/employees?year=2026&month=1&planning_unit_ids=101&planning_unit_ids=102").status_code == 200
        assert client.get("/employees?year=2026&month=1&planning_unit_ids=201").status_code == 409
        assert client.get("/employees?year=2026&month=1&planning_unit_ids=-1").status_code == 422
        assert client.get("/employees?year=2026&month=13&planning_unit_ids=101").status_code == 422
        source.missing_account = True
        response = client.get("/employees?year=2026&month=1&planning_unit_ids=101&planning_unit_ids=102")
        assert response.status_code == 409
        assert "employees" not in response.json()
        assert "TPersonal" not in response.text
    finally:
        app.dependency_overrides.clear()


def test_explicit_zero_target_and_actual_are_preserved_missing_target_is_error() -> None:
    row = TimeOfficeMonthlyWorkAccountRow(employee_id=1, month=202601, target_hours=0, actual_hours=0)
    account = map_monthly_work_accounts((row,))[0]
    assert account.target_minutes == 0
    assert account.actual_minutes == 0
    assert account.credited_minutes is None
    with pytest.raises(ValueError, match="Missing"):
        map_monthly_work_accounts((row.model_copy(update={"target_hours": None}),))


@pytest.mark.parametrize("defect", ["credit_date", "duplicate_credit", "restriction_identity", "ambiguous_home"])
def test_declared_evidence_is_validated_before_any_employee_is_returned(defect: str) -> None:
    source = InspectionSource()
    original_execute = source.execute

    def malformed_execute(query: Any, params: dict[str, Any]) -> MagicMock:
        result = original_execute(query, params)
        rows = result.mappings.return_value.all.return_value
        if "StaffSchedulingEmployeeMonthEvidence" in str(query):
            credits = json.loads(rows[0]["credit_details"])
            if defect == "credit_date":
                credits[0]["date"] = "2025-12-31"
            elif defect == "duplicate_credit":
                credits.append(credits[0])
            elif defect == "restriction_identity":
                rows[0]["hard_restrictions"] = json.dumps(
                    [{"employee_id": 999, "date": "2026-01-01", "availability_type": "unavailable"}]
                )
            rows[0]["credit_details"] = json.dumps(credits)
        elif "TPlanungseinheitenPersonal" in str(query) and defect == "ambiguous_home":
            rows[1]["is_home"] = True
        return result

    source.connection.execute.side_effect = malformed_execute
    with pytest.raises(ValueError, match="outside|Duplicate|match|origin"):
        source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=PlanningMonth(year=2026, month=1))
