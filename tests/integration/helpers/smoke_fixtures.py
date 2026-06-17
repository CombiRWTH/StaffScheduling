from dataclasses import dataclass
from datetime import date, timedelta

from legacy.src.employee import Employee
from legacy.src.shift import Shift

type WeekdayAbbreviation = str
type EmployeeLevel = str
type ShiftAbbreviation = str
type MinStaffing = dict[EmployeeLevel, dict[WeekdayAbbreviation, dict[ShiftAbbreviation, int]]]


SMOKE_TEST_WEIGHTS: dict[str, int] = {
    "free_weekend": 1,
    "consecutive_nights": 1,
    "hidden": 1,
    "overtime": 1,
    "consecutive_days": 1,
    "rotate": 1,
    "wishes": 1,
    "after_night": 1,
    "second_weekend": 1,
    "preferred_block": 1,
}


@dataclass(frozen=True)
class SmokeSolveFixture:
    unit: int
    start_date: date
    end_date: date
    days: list[date]
    shifts: list[Shift]
    employees: list[Employee]
    min_staffing: MinStaffing


def make_smoke_solve_fixture() -> SmokeSolveFixture:
    """Small clean fixture for one full service-level solver run."""
    start_date = date(2024, 11, 2)  # Saturday
    days = [start_date + timedelta(days=offset) for offset in range(2)]

    return SmokeSolveFixture(
        unit=999,
        start_date=start_date,
        end_date=days[-1],
        days=days,
        shifts=make_solver_compatible_shifts(),
        employees=[
            make_employee(
                key=1,
                name="Alice",
                level="Fachkraft",
                target_working_time=460,
            ),
            make_employee(
                key=2,
                name="Bob",
                level="Fachkraft",
                target_working_time=460,
            ),
        ],
        min_staffing={
            "Fachkraft": make_weekend_early_staffing(),
        },
    )


def make_solver_compatible_shifts() -> list[Shift]:
    return [
        Shift(Shift.EARLY, "Früh", 360, 820),
        Shift(Shift.INTERMEDIATE, "Zwischen", 480, 940),
        Shift(Shift.LATE, "Spät", 805, 1265),
        Shift(Shift.NIGHT, "Nacht", 1250, 375),
        Shift(Shift.MANAGEMENT, "Z60", 480, 840),
        Shift(5, "F2_", 360, 820),
        Shift(6, "S2_", 805, 1265),
        Shift(7, "N5", 1250, 375),
    ]


def make_employee(
    *,
    key: int,
    name: str,
    level: str,
    target_working_time: int,
) -> Employee:
    return Employee(
        key=key,
        surname="Smoke",
        name=name,
        level=level,
        type=f"Test-{level}",
        target_working_time=target_working_time,
        actual_working_time=0,
        forbidden_days=[],
        forbidden_shifts=[],
        vacation_days=[],
        vacation_shifts=[],
        wish_days=[],
        wish_shifts=[],
        planned_shifts=[],
        qualifications=[],
    )


def make_weekend_early_staffing() -> dict[str, dict[str, int]]:
    staffing = make_empty_week_staffing()
    staffing["Sa"]["F"] = 1
    staffing["So"]["F"] = 1
    return staffing


def make_empty_week_staffing() -> dict[str, dict[str, int]]:
    return {
        "Mo": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Di": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Mi": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Do": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Fr": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Sa": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "So": {"F": 0, "Z": 0, "S": 0, "N": 0},
    }
