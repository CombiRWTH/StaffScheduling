"""The readable tables of a month's schedule: one row per duty, per employee, per staffing need and per gap.

Review and the CSV files show the same rows, so a reviewed schedule and its downloads cannot differ.
"""

from collections import Counter
from collections.abc import Iterable
from datetime import date as Date
from datetime import datetime

from app.domain.assignment import Assignment
from app.domain.availability import Availability
from app.domain.calendar import public_holiday
from app.domain.core import SchedulingBaseModel
from app.domain.dataset import SchedulingDataset
from app.domain.demand import DemandKey
from app.domain.duty import PLANNING_TIMEZONE, duty_times
from app.domain.employee import StaffLevel
from app.domain.monthly_work_account import WorkCredit
from app.domain.planning_unit import PlanningUnitMembership, PlanningUnitType, home_unit_id
from app.domain.shift import ShiftType


class DutyRow(SchedulingBaseModel):
    """One assignment with readable labels, real times and the employee's origin."""

    employee_id: int
    employee_name: str
    date: Date
    weekday: int
    """ISO weekday, Monday=1 to Sunday=7; also on a public holiday."""
    is_public_holiday: bool
    planning_unit_id: int
    """The station where the duty is worked."""
    planning_unit_name: str
    shift_id: int
    shift_code: str
    shift_type: ShiftType
    start_at: datetime
    """Europe/Berlin time with its UTC offset."""
    end_at: datetime
    """Europe/Berlin time with its UTC offset; a night ends on the next date."""
    net_work_minutes: int
    """Paid minutes booked on the monthly account."""
    staff_level: StaffLevel
    """The qualification credited towards demand."""
    origin_unit_id: int | None
    """The employee's home station or jumper pool on the date; empty only when the employee has no
    membership that day, which the schedule check reports as an eligibility finding."""
    origin_unit_name: str | None
    origin_unit_type: PlanningUnitType | None


class EmployeeRow(SchedulingBaseModel):
    """One participating employee's month, also without duties."""

    employee_id: int
    employee_name: str
    staff_level: StaffLevel
    """Employee-level qualification; each duty states the qualification it is credited as."""
    planning_month: str
    """`YYYY-MM`."""
    target_minutes: int
    credited_minutes: int
    """Verified credits: approved absences and trusted work, each counted once."""
    generated_minutes: int
    """Paid minutes of the month's duties."""
    balance_minutes: int
    """Generated plus credited minus target minutes."""
    memberships: tuple[PlanningUnitMembership, ...]
    hard_availability: tuple[Availability, ...]
    """Approved absences and restrictions of the month; all of them bind planning."""
    credit_details: tuple[WorkCredit, ...]


class StaffingRow(SchedulingBaseModel):
    """Required against assigned staff of one station, date, shift and qualification."""

    planning_unit_id: int
    date: Date
    shift_id: int
    staff_level: StaffLevel
    required_count: int
    """Zero where nobody is required but someone is assigned."""
    assigned_count: int


class GapRow(SchedulingBaseModel):
    """Required slots of one station, date, shift and qualification that no duty fills."""

    planning_unit_id: int
    planning_unit_name: str
    date: Date
    shift_id: int
    shift_code: str
    staff_level: StaffLevel
    required_count: int
    assigned_count: int
    missing_count: int


class ScheduleTables(SchedulingBaseModel):
    duties: tuple[DutyRow, ...]
    employees: tuple[EmployeeRow, ...]
    staffing: tuple[StaffingRow, ...]
    gaps: tuple[GapRow, ...]


def schedule_tables(dataset: SchedulingDataset, assignments: Iterable[Assignment]) -> ScheduleTables:
    """The tables of the month's assignments.

    Every assignment must reference the dataset, which a schedule check without input findings proves.
    Duties are sorted by date, station, start and employee; employees, staffing and gaps by their IDs.
    """
    employees = {row.employee_id: row for row in dataset.employees}
    units = {row.planning_unit_id: row for row in dataset.planning_units}
    shifts = {row.shift_id: row for row in dataset.shifts}
    assignments = tuple(assignments)

    duties: list[DutyRow] = []
    for row in assignments:
        shift = shifts[row.shift_id]
        times = duty_times(row.date, shift)
        home = home_unit_id(dataset.planning_unit_memberships, row.employee_id, row.date)
        origin = units[home] if home is not None else None
        duties.append(
            DutyRow(
                employee_id=row.employee_id,
                employee_name=employees[row.employee_id].display_name,
                date=row.date,
                weekday=row.date.isoweekday(),
                is_public_holiday=public_holiday(row.date) is not None,
                planning_unit_id=row.planning_unit_id,
                planning_unit_name=units[row.planning_unit_id].display_name,
                shift_id=shift.shift_id,
                shift_code=shift.code,
                shift_type=shift.type,
                start_at=times.start.astimezone(PLANNING_TIMEZONE),
                end_at=times.end.astimezone(PLANNING_TIMEZONE),
                net_work_minutes=shift.net_work_minutes,
                staff_level=row.staff_level,
                origin_unit_id=origin.planning_unit_id if origin else None,
                origin_unit_name=origin.display_name if origin else None,
                origin_unit_type=origin.type if origin else None,
            )
        )
    duties.sort(key=lambda row: (row.date, row.planning_unit_id, row.start_at, row.employee_id))

    generated = Counter[int]()
    for row in assignments:
        generated[row.employee_id] += shifts[row.shift_id].net_work_minutes
    rows: list[EmployeeRow] = []
    for account in sorted(dataset.monthly_work_accounts, key=lambda row: row.employee_id):
        employee = employees[account.employee_id]
        rows.append(
            EmployeeRow(
                employee_id=employee.employee_id,
                employee_name=employee.display_name,
                staff_level=employee.staff_level,
                planning_month=dataset.planning_month.label,
                target_minutes=account.target_minutes,
                credited_minutes=account.credited_minutes,
                generated_minutes=generated[employee.employee_id],
                balance_minutes=account.balance(generated[employee.employee_id]),
                memberships=tuple(
                    row for row in dataset.planning_unit_memberships if row.employee_id == employee.employee_id
                ),
                hard_availability=tuple(row for row in dataset.availability if row.employee_id == employee.employee_id),
                credit_details=account.credit_details,
            )
        )

    required = Counter[DemandKey]()
    for row in dataset.demand_requirements:
        required[row.demand_key] += row.required_count
    assigned = Counter(row.demand_key for row in assignments)
    staffing = tuple(
        StaffingRow(
            planning_unit_id=unit_id,
            date=day,
            shift_id=shift_id,
            staff_level=level,
            required_count=required[(unit_id, day, shift_id, level)],
            assigned_count=assigned[(unit_id, day, shift_id, level)],
        )
        for unit_id, day, shift_id, level in sorted({*required, *assigned})
    )
    gaps = tuple(
        GapRow(
            planning_unit_id=row.planning_unit_id,
            planning_unit_name=units[row.planning_unit_id].display_name,
            date=row.date,
            shift_id=row.shift_id,
            shift_code=shifts[row.shift_id].code,
            staff_level=row.staff_level,
            required_count=row.required_count,
            assigned_count=row.assigned_count,
            missing_count=row.required_count - row.assigned_count,
        )
        for row in staffing
        if row.assigned_count < row.required_count
    )
    return ScheduleTables(duties=tuple(duties), employees=tuple(rows), staffing=staffing, gaps=gaps)
