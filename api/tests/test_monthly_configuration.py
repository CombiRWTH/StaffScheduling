from collections.abc import Iterator
from datetime import date
from typing import cast

import httpx
import pytest
from fastapi.testclient import TestClient
from inspection_fixture import InspectionSource

from app.api.planning import get_planning_source
from app.domain import (
    Availability,
    AvailabilityType,
    DayType,
    DemandPattern,
    DemandRequirement,
    InvalidSelection,
    MonthlyDemand,
    PatternRequirement,
    PlanningMonth,
    StaffLevel,
    Wish,
    WishType,
    expand_pattern,
    month_calendar,
)
from app.main import app
from app.timeoffice import TimeOfficeUnavailable

JANUARY = PlanningMonth(year=2026, month=1)
EARLY, INTERMEDIATE, LATE, NIGHT = 1113, 1453, 1605, 1690


@pytest.fixture
def source() -> InspectionSource:
    return InspectionSource()


@pytest.fixture
def client(source: InspectionSource) -> Iterator[httpx.Client]:
    app.dependency_overrides[get_planning_source] = lambda: source.service
    try:
        yield cast(httpx.Client, TestClient(app))
    finally:
        app.dependency_overrides.clear()


def availability(employee_id: int, day: int, **fields: object) -> Availability:
    return Availability.model_validate(
        {"employee_id": employee_id, "date": date(2026, 1, day), "availability_type": "unavailable", **fields}
    )


def test_availability_writes_touch_only_their_employee_and_date(source: InspectionSource) -> None:
    service = source.service
    service.save_availability(availability(1, 5, availability_type="available_only", shift_ids=(EARLY, LATE)))
    service.save_availability(availability(1, 6, reason="Fortbildung extern"))
    service.save_availability(availability(2, 5))

    service.save_availability(availability(1, 5, availability_type="vacation"))
    service.delete_availability(employee_id=1, day=date(2026, 1, 6))

    calendar = service.get_employee_calendar(employee_id=1, planning_month=JANUARY)
    assert [(row.date.day, row.availability_type) for row in calendar.availability] == [(5, AvailabilityType.VACATION)]
    # The native approved absence is read separately and survives every project write.
    assert [(row.date.day, row.reason) for row in calendar.absences] == [(1, "U")]
    assert calendar.wishes == ()
    assert [shift.code for shift in calendar.shifts] == ["F", "Z", "S", "N"]
    other = service.get_employee_calendar(employee_id=2, planning_month=JANUARY)
    assert [row.date.day for row in other.availability] == [5]

    inspected = service.inspect_employees(planning_unit_ids=(101,), planning_month=JANUARY).employees[0]
    assert {(row.date.day, row.source) for row in inspected.availability} == {
        (1, "TimeOffice absence"),
        (5, "Project availability"),
    }


def test_reason_and_shifts_survive_read_back(source: InspectionSource) -> None:
    saved = availability(3, 9, availability_type="available_only", shift_ids=(NIGHT,), reason="Nur Nacht")
    source.service.save_availability(saved)
    [read] = source.service.get_employee_calendar(employee_id=3, planning_month=JANUARY).availability
    assert read.model_dump(exclude={"source"}) == saved.model_dump(exclude={"source"})


def test_wishes_are_separate_from_availability(source: InspectionSource) -> None:
    service = source.service
    service.save_availability(availability(1, 7))
    service.save_wish(Wish(employee_id=1, date=date(2026, 1, 7), type=WishType.FREE_SHIFT, shift_id=NIGHT))
    service.save_wish(Wish(employee_id=1, date=date(2026, 1, 7), type=WishType.PREFERRED_DAY))
    calendar = service.get_employee_calendar(employee_id=1, planning_month=JANUARY)
    assert [(row.date.day, row.type) for row in calendar.wishes] == [(7, WishType.PREFERRED_DAY)]
    assert [row.date.day for row in calendar.availability] == [7]

    service.delete_wish(employee_id=1, day=date(2026, 1, 7))
    calendar = service.get_employee_calendar(employee_id=1, planning_month=JANUARY)
    assert calendar.wishes == ()
    assert [row.date.day for row in calendar.availability] == [7]


def test_invalid_or_failed_writes_leave_saved_entries_unchanged(source: InspectionSource) -> None:
    service = source.service
    service.save_availability(availability(1, 5))
    before = source.tables["StaffSchedulingAvailability"].copy()

    with pytest.raises(InvalidSelection, match="no planning membership"):
        service.save_availability(availability(999, 5))
    with pytest.raises(InvalidSelection, match="Unknown shift"):
        service.save_availability(availability(1, 5, availability_type="available_only", shift_ids=(42,)))
    with pytest.raises(InvalidSelection, match="Unknown shift"):
        service.save_wish(Wish(employee_id=1, date=date(2026, 1, 5), type=WishType.FREE_SHIFT, shift_id=42))
    source.failing_ids = {1}
    with pytest.raises(TimeOfficeUnavailable):
        service.save_availability(availability(1, 5, availability_type="vacation"))

    assert source.tables["StaffSchedulingAvailability"] == before


def _requirement(day: int, shift_id: int, level: StaffLevel, count: int, unit: int = 101) -> DemandRequirement:
    return DemandRequirement(
        planning_unit_id=unit, date=date(2026, 1, day), shift_id=shift_id, staff_level=level, required_count=count
    )


def test_dated_demand_round_trips_per_station_month(source: InspectionSource) -> None:
    service = source.service
    unsaved = service.get_demand(planning_unit_id=101, planning_month=JANUARY)
    assert unsaved.demand is None
    assert len(unsaved.calendar) == 31
    assert unsaved.calendar[0].public_holiday == "Neujahr"

    north = MonthlyDemand(
        planning_unit_id=101,
        planning_month=JANUARY,
        requirements=(
            _requirement(1, EARLY, StaffLevel.PROFESSIONAL, 2),
            _requirement(2, EARLY, StaffLevel.PROFESSIONAL, 3),
            _requirement(2, INTERMEDIATE, StaffLevel.MFA, 1),
        ),
    )
    south = MonthlyDemand(
        planning_unit_id=102,
        planning_month=JANUARY,
        requirements=(_requirement(3, NIGHT, StaffLevel.ASSISTANT, 1, 102),),
    )
    service.save_demand(north)
    service.save_demand(south)
    assert service.get_demand(planning_unit_id=101, planning_month=JANUARY).demand == north

    service.save_demand(MonthlyDemand(planning_unit_id=101, planning_month=JANUARY, requirements=()))
    emptied = service.get_demand(planning_unit_id=101, planning_month=JANUARY).demand
    assert emptied is not None
    assert emptied.requirements == ()
    assert service.get_demand(planning_unit_id=102, planning_month=JANUARY).demand == south


def test_demand_rejects_pools_unplanned_months_and_unknown_shifts(source: InspectionSource) -> None:
    service = source.service
    with pytest.raises(InvalidSelection, match="shared pool"):
        service.get_demand(planning_unit_id=201, planning_month=JANUARY)
    with pytest.raises(InvalidSelection, match="No TimeOffice target plan"):
        service.save_demand(
            MonthlyDemand(planning_unit_id=101, planning_month=PlanningMonth(year=2026, month=2), requirements=())
        )
    with pytest.raises(InvalidSelection, match="Unknown shift"):
        service.save_demand(
            MonthlyDemand(
                planning_unit_id=101, planning_month=JANUARY, requirements=(_requirement(1, 42, StaffLevel.MFA, 1),)
            )
        )
    assert source.tables["StaffSchedulingDemandMonth"] == []


def test_nrw_calendar_keeps_the_weekday_and_marks_regional_holidays() -> None:
    june = month_calendar(PlanningMonth(year=2026, month=6))
    corpus_christi = june[3]
    assert corpus_christi.public_holiday == "Fronleichnam"
    assert corpus_christi.weekday == 4
    assert corpus_christi.day_type == DayType.HOLIDAY
    assert june[4].day_type == DayType.FRIDAY


def test_pattern_applies_weekday_rows_and_the_holiday_row() -> None:
    april = PlanningMonth(year=2026, month=4)
    demand = expand_pattern(
        DemandPattern(
            planning_unit_id=101,
            planning_month=april,
            cells=(
                PatternRequirement(
                    day_type=DayType.FRIDAY, shift_id=EARLY, staff_level=StaffLevel.MFA, required_count=2
                ),
                PatternRequirement(
                    day_type=DayType.HOLIDAY, shift_id=EARLY, staff_level=StaffLevel.MFA, required_count=1
                ),
                PatternRequirement(
                    day_type=DayType.MONDAY, shift_id=LATE, staff_level=StaffLevel.MFA, required_count=0
                ),
            ),
        )
    )
    by_date = {row.date.day: row.required_count for row in demand.requirements}
    # Good Friday (3rd) and Easter Monday (6th) take the holiday row; zero cells produce no requirement.
    assert by_date == {3: 1, 6: 1, 10: 2, 17: 2, 24: 2}


def test_http_contract_validates_before_saving(source: InspectionSource, client: httpx.Client) -> None:
    put = client.put("/availability/1/2026-01-05", json={"availability_type": "available_only", "shift_ids": [EARLY]})
    assert put.status_code == 200
    assert client.get("/availability?employee_id=1&year=2026&month=1").json()["availability"][0]["shift_ids"] == [EARLY]

    for body in (
        {"availability_type": "available_only"},
        {"availability_type": "vacation", "shift_ids": [EARLY]},
        {"availability_type": "vacation", "reason": "  "},
        {"availability_type": "sick"},
    ):
        assert client.put("/availability/1/2026-01-06", json=body).status_code == 422
    assert client.put("/availability/999/2026-01-06", json={"availability_type": "vacation"}).status_code == 422
    assert client.put("/wishes/1/2026-01-06", json={"type": "free_shift"}).status_code == 422
    assert client.put("/wishes/1/2026-01-06", json={"type": "free_day"}).status_code == 200
    assert client.delete("/wishes/1/2026-01-06").status_code == 204
    assert client.delete("/availability/1/2026-01-05").status_code == 204
    assert source.tables["StaffSchedulingAvailability"] == []
    assert source.tables["StaffSchedulingWish"] == []

    month = {"year": 2026, "month": 1}
    row = {"planning_unit_id": 101, "date": "2026-01-02", "shift_id": EARLY, "staff_level": "mfa", "required_count": 1}
    for requirements in ([{**row, "date": "2026-02-01"}], [row, row], [{**row, "required_count": 0}]):
        body = {"planning_unit_id": 101, "planning_month": month, "requirements": requirements}
        assert client.put("/demand", json=body).status_code == 422
    assert source.tables["StaffSchedulingDemand"] == []
    assert client.put(
        "/demand", json={"planning_unit_id": 101, "planning_month": month, "requirements": [row]}
    ).is_success
    assert client.get("/demand?planning_unit_id=101&year=2026&month=1").json()["demand"]["requirements"] == [row]

    cell = {"day_type": "holiday", "shift_id": EARLY, "staff_level": "mfa", "required_count": 1}
    preview = client.post("/demand/pattern", json={"planning_unit_id": 101, "planning_month": month, "cells": [cell]})
    assert [requirement["date"] for requirement in preview.json()["requirements"]] == ["2026-01-01"]
    duplicate = {"planning_unit_id": 101, "planning_month": month, "cells": [cell, cell]}
    assert client.post("/demand/pattern", json=duplicate).status_code == 422
