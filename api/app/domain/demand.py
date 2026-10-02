"""Dated minimum staffing per station, shift and qualification, and the weekly pattern that fills it."""

from datetime import date as Date
from typing import Self

from pydantic import Field, model_validator

from app.domain.calendar import CalendarDay, DayType, month_calendar
from app.domain.core import SchedulingBaseModel
from app.domain.employee import StaffLevel
from app.domain.planning_month import PlanningMonth
from app.domain.planning_unit import PlanningUnitId
from app.domain.shift import ShiftId, ShiftOption


class DemandRequirement(SchedulingBaseModel):
    """Hard minimum staffing demand for one planning unit, date, shift and staff level."""

    planning_unit_id: PlanningUnitId
    date: Date
    shift_id: ShiftId
    staff_level: StaffLevel
    required_count: int = Field(gt=0)


class MonthlyDemand(SchedulingBaseModel):
    """The complete demand of one station month; an omitted date/shift/qualification requires nobody."""

    planning_unit_id: PlanningUnitId
    planning_month: PlanningMonth
    requirements: tuple[DemandRequirement, ...]

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        keys = [(row.date, row.shift_id, row.staff_level) for row in self.requirements]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate demand for one date, shift and qualification.")
        for row in self.requirements:
            if row.planning_unit_id != self.planning_unit_id:
                raise ValueError("Demand requirement belongs to another station.")
            if not self.planning_month.start <= row.date <= self.planning_month.end:
                raise ValueError("Demand date is outside the planning month.")
        return self


class DemandConfiguration(SchedulingBaseModel):
    """What the staffing editor shows for one station month; `demand` is None until a month is saved."""

    planning_unit_id: PlanningUnitId
    planning_month: PlanningMonth
    demand: MonthlyDemand | None
    calendar: tuple[CalendarDay, ...]
    shifts: tuple[ShiftOption, ...]


class PatternRequirement(SchedulingBaseModel):
    """One cell of a weekly pattern: how many of a qualification a shift needs on a day type."""

    day_type: DayType
    shift_id: ShiftId
    staff_level: StaffLevel
    required_count: int = Field(ge=0)


class DemandPattern(SchedulingBaseModel):
    """A weekly pattern for one station month: Monday to Sunday plus a holiday row."""

    planning_unit_id: PlanningUnitId
    planning_month: PlanningMonth
    cells: tuple[PatternRequirement, ...]

    @model_validator(mode="after")
    def validate_cells(self) -> Self:
        keys = [(row.day_type, row.shift_id, row.staff_level) for row in self.cells]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate pattern cell.")
        return self


def expand_pattern(pattern: DemandPattern) -> MonthlyDemand:
    """Apply a weekly pattern to every date of the month; NRW public holidays take the holiday row."""
    return MonthlyDemand(
        planning_unit_id=pattern.planning_unit_id,
        planning_month=pattern.planning_month,
        requirements=tuple(
            DemandRequirement(
                planning_unit_id=pattern.planning_unit_id,
                date=day.date,
                shift_id=cell.shift_id,
                staff_level=cell.staff_level,
                required_count=cell.required_count,
            )
            for day in month_calendar(pattern.planning_month)
            for cell in pattern.cells
            if cell.day_type == day.day_type and cell.required_count
        ),
    )
