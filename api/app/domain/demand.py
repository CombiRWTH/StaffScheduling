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

# Station, date, shift and credited qualification: what a demand row requires and a duty covers.
type DemandKey = tuple[PlanningUnitId, Date, ShiftId, StaffLevel]


class DemandRequirement(SchedulingBaseModel):
    """Minimum staffing demand for one planning unit, date, shift and staff level; an unfilled slot is a gap."""

    planning_unit_id: PlanningUnitId
    date: Date
    shift_id: ShiftId
    staff_level: StaffLevel
    required_count: int = Field(gt=0)

    @property
    def demand_key(self) -> DemandKey:
        return (self.planning_unit_id, self.date, self.shift_id, self.staff_level)


class Gap(SchedulingBaseModel):
    """Required slots of one demand row that no assignment fills (Lücke).

    Gaps are reported next to the assignments, never as assignments, so guest staff can be requested
    for them; publication writes only duties.
    """

    planning_unit_id: PlanningUnitId
    date: Date
    shift_id: ShiftId
    staff_level: StaffLevel
    missing_count: int = Field(gt=0)

    @property
    def demand_key(self) -> DemandKey:
        return (self.planning_unit_id, self.date, self.shift_id, self.staff_level)


# An upper bound that no station reaches, so a typo cannot save an absurd minimum.
MAX_REQUIRED_COUNT = 99


class DemandCell(SchedulingBaseModel):
    """How many of a qualification one shift needs on one date of the month's station."""

    date: Date
    shift_id: ShiftId
    staff_level: StaffLevel
    required_count: int = Field(gt=0, le=MAX_REQUIRED_COUNT)


class MonthlyDemand(SchedulingBaseModel):
    """The complete demand of one station month; an omitted date/shift/qualification requires nobody."""

    planning_unit_id: PlanningUnitId
    planning_month: PlanningMonth
    cells: tuple[DemandCell, ...]

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        keys = [(cell.date, cell.shift_id, cell.staff_level) for cell in self.cells]
        if len(set(keys)) != len(keys):
            raise ValueError("Duplicate demand for one date, shift and qualification.")
        if any(cell.date not in self.planning_month for cell in self.cells):
            raise ValueError("Demand date is outside the planning month.")
        return self

    @property
    def requirements(self) -> tuple[DemandRequirement, ...]:
        """The cells as solver requirements of this station."""
        return tuple(
            DemandRequirement(planning_unit_id=self.planning_unit_id, **cell.model_dump()) for cell in self.cells
        )


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
    required_count: int = Field(ge=0, le=MAX_REQUIRED_COUNT)


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
        cells=tuple(
            DemandCell(
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
