from collections.abc import Callable
from datetime import date, datetime
from typing import Any, cast
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient
from inspection_fixture import InspectionSource

from app.api.shared import get_planning_source
from app.domain import PlanningMonth, StaffLevel
from app.main import app

RowChange = Callable[[list[dict[str, Any]]], None]


def with_rows(source: InspectionSource, table: str, change: RowChange) -> None:
    """Edit the fictional rows one query returns before the adapter translates them."""
    previous = source.connection.execute.side_effect

    def execute(query: Any, params: dict[str, Any]) -> MagicMock:
        result = previous(query, params)
        rows = result.mappings.return_value.all.return_value
        if table in str(query) and rows:
            change(rows)
        return result

    source.connection.execute.side_effect = execute


def _set(column: str, value: Any, index: int = 0) -> RowChange:
    def change(rows: list[dict[str, Any]]) -> None:
        rows[index][column] = value

    return change


def test_combined_scope_retains_identity_memberships_mfa_origin_and_account_evidence() -> None:
    source = InspectionSource()
    month = PlanningMonth(year=2026, month=1)
    result = source.service.inspect_employees(planning_unit_ids=(101, 102, 101), planning_month=month)
    assert result.selected_station_ids == (101, 102)
    assert result.associated_jumper_pool_ids == (201,)
    assert [employee.employee_id for employee in result.employees] == [1, 2, 3]
    employee = result.employees[0]
    assert employee.staff_level == StaffLevel.MFA
    assert {row.planning_unit_id for row in employee.memberships if row.is_home} == {201}
    assert {row.planning_unit_id for row in employee.memberships if row.is_replacement} == {101, 102}
    assert len(employee.memberships) == 3
    assert employee.account.target_minutes == 9600
    assert employee.account.actual_minutes == 0
    assert employee.account.credited_minutes == 480
    assert employee.account.credit_details[0].source == "TimeOffice U absence"
    assert result.employees[1].account.credit_details == ()
    assert employee.availability[0].date == date(2026, 1, 1)
    assert employee.availability[0].reason == "U"
    # A pool origin alone does not imply eligibility at either destination.
    assert {row.planning_unit_id for row in result.employees[2].memberships} == {201}
    source.name = "Renamed Example"
    renamed = source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=month)
    assert renamed.employees[0].employee_id == employee.employee_id
    assert renamed.employees[0].display_name == "Renamed Example"
    assert not any(word in sql.upper() for sql in source.queries for word in ("CREATE TABLE", "INSERT ", "DELETE "))
    assert not any("FROM TPlanPersonal " in sql for sql in source.queries)

    with_rows(source, "AS roster_date", lambda rows: rows.append({**rows[0], "resolved_absence_code": "ZU"}))
    distinct = source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=month)
    assert {row.reason for row in distinct.employees[0].availability} == {"U", "ZU"}


@pytest.mark.parametrize(
    "flag",
    ["orphan_credit", "missing_account", "missing_employee", "duplicate_account", "duplicate_plan", "missing_name"],
)
def test_missing_or_ambiguous_source_facts_fail_the_whole_inspection(flag: str) -> None:
    source = InspectionSource()
    if flag == "missing_name":
        source.name = ""
    else:
        setattr(source, flag, True)
    with pytest.raises(ValueError, match="requires|require|Missing|Multiple|has no 'SC' absence"):
        source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=PlanningMonth(year=2026, month=1))


def test_options_full_month_and_http_failure_contract() -> None:
    source = InspectionSource()
    app.dependency_overrides[get_planning_source] = lambda: source.service
    try:
        client = cast(httpx.Client, TestClient(app))
        response = client.get("/planning/options?year=2026&month=2")
        assert response.status_code == 200
        assert [row["planning_unit_id"] for row in response.json()["planning_units"]] == [102]
        assert response.json()["planning_month"]["end"] == "2026-02-28"
        assert client.get("/employees?year=2026&month=1&planning_unit_ids=101&planning_unit_ids=102").status_code == 200
        assert client.get("/employees?year=2026&month=1&planning_unit_ids=201").status_code == 422
        assert client.get("/employees?year=2026&month=2&planning_unit_ids=101").status_code == 422
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
    source = InspectionSource()
    target_hours: list[float | None] = [0.0]

    def set_hours(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            row.update(target_hours=target_hours[0], actual_hours=0.0)

    with_rows(source, "TPersonalKontenJeMonat", set_hours)
    month = PlanningMonth(year=2026, month=1)
    account = source.service.inspect_employees(planning_unit_ids=(101,), planning_month=month).employees[0].account
    assert account.target_minutes == 0
    assert account.actual_minutes == 0
    target_hours[0] = None
    with pytest.raises(ValueError, match="Missing"):
        source.service.inspect_employees(planning_unit_ids=(101,), planning_month=month)


@pytest.mark.parametrize("defect", ["credit_date", "duplicate_credit", "unknown_shift", "ambiguous_home"])
def test_month_facts_are_validated_before_any_employee_is_returned(defect: str) -> None:
    source = InspectionSource()

    def malformed_credits(rows: list[dict[str, Any]]) -> None:
        if defect == "credit_date":
            rows[0]["credit_date"] = datetime(2025, 12, 31)
        elif defect == "duplicate_credit":
            rows.append(dict(rows[0]))

    if defect == "ambiguous_home":
        with_rows(source, "TPlanungseinheitenPersonal", _set("is_home", True, index=1))
    elif defect == "unknown_shift":
        source.tables["StaffSchedulingAvailability"].append(
            {
                "employee_id": 2,
                "availability_date": date(2026, 1, 2),
                "availability_type": "available_only",
                "shift_ids": "[9999]",
                "reason": None,
            }
        )
    else:
        with_rows(source, "TPersonalKontenJeTag", malformed_credits)
    with pytest.raises(ValueError, match="outside|Duplicate|Unknown allowed shift|origin"):
        source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=PlanningMonth(year=2026, month=1))


def test_source_codes_are_trimmed_and_ignored_absences_are_dropped() -> None:
    source = InspectionSource()

    def pad(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            row["membership_profession_code"] = f" {row['membership_profession_code']} "

    with_rows(source, "TPlanungseinheitenPersonal", pad)
    with_rows(source, "AS roster_date", _set("resolved_absence_code", "FR"))
    result = source.service.inspect_employees(
        planning_unit_ids=(101, 102), planning_month=PlanningMonth(year=2026, month=1)
    )

    assert result.employees[0].memberships[0].staff_level == StaffLevel.MFA
    assert result.employees[0].availability == ()


@pytest.mark.parametrize(
    ("table", "change", "message"),
    [
        ("AS roster_date", _set("resolved_absence_code", "XX"), "Unmapped TimeOffice absence code"),
        ("TPlanungseinheitenPersonal", _set("membership_profession_code", "00000-000"), "No qualification mapping"),
        ("TPersonal per", _set("employee_profession_code", None), "No qualification mapping"),
        ("JOIN TPlan p", _set("plan_planning_unit_id", 999), "different planning unit"),
        ("TPlanungseinheitenPersonal", _set("is_home", False, index=3), "home origin"),
        ("FROM TPlanungseinheiten pe", _set("planning_unit_code", "   "), "display names"),
    ],
    ids=[
        "unmapped_absence",
        "unmapped_membership_profession",
        "missing_employee_profession",
        "foreign_plan",
        "replacement_only_origin",
        "blank_unit_name",
    ],
)
def test_untranslatable_source_facts_fail_the_whole_inspection(table: str, change: RowChange, message: str) -> None:
    source = InspectionSource()
    with_rows(source, table, change)

    with pytest.raises(ValueError, match=message):
        source.service.inspect_employees(planning_unit_ids=(101, 102), planning_month=PlanningMonth(year=2026, month=1))


def test_selected_station_without_target_plan_fails() -> None:
    source = InspectionSource()

    with pytest.raises(ValueError, match="No TimeOffice target plan"):
        source.service.inspect_employees(planning_unit_ids=(101,), planning_month=PlanningMonth(year=2026, month=2))


def test_replacement_only_pool_membership_is_not_an_association() -> None:
    source = InspectionSource()

    def pool_as_replacement(rows: list[dict[str, Any]]) -> None:
        for row in rows:
            if row["employee_id"] == 1:
                row["is_home"] = row["planning_unit_id"] == 101
                row["is_replacement"] = row["planning_unit_id"] != 101

    with_rows(source, "TPlanungseinheitenPersonal", pool_as_replacement)
    result = source.service.inspect_employees(
        planning_unit_ids=(101,), planning_month=PlanningMonth(year=2026, month=1)
    )

    assert result.associated_jumper_pool_ids == ()
    assert [employee.employee_id for employee in result.employees] == [1, 2]
    assert 201 in {unit.planning_unit_id for unit in result.planning_units}
