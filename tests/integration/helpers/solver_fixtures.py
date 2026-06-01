from dataclasses import dataclass
from datetime import date, timedelta

from src.employee import Employee
from src.shift import Shift

type WeekdayAbbreviation = str
type EmployeeLevel = str
type ShiftAbbreviation = str
type MinStaffing = dict[EmployeeLevel, dict[WeekdayAbbreviation, dict[ShiftAbbreviation, int]]]


TEST_SOLVER_WEIGHTS: dict[str, int] = {
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
class CleanSolverFixture:
    unit: int
    start_date: date
    end_date: date
    days: list[date]
    shifts: list[Shift]
    employees: list[Employee]
    min_staffing: MinStaffing


def make_standard_shifts() -> list[Shift]:
    return [
        Shift(Shift.EARLY, "Früh", 360, 820),
        Shift(Shift.INTERMEDIATE, "Zwischen", 480, 940),
        Shift(Shift.LATE, "Spät", 805, 1265),
        Shift(Shift.NIGHT, "Nacht", 1250, 375),
    ]


def make_days(start_date: date, number_of_days: int) -> list[date]:
    return [start_date + timedelta(days=offset) for offset in range(number_of_days)]


def make_employee(
    *,
    key: int,
    name: str,
    level: str,
    target_working_time: int,
    forbidden_days: list[int] | None = None,
    wish_days: list[int] | None = None,
    wish_shifts: list[tuple[int, str]] | None = None,
    qualifications: list[str] | None = None,
) -> Employee:
    return Employee(
        key=key,
        surname="Clean",
        name=name,
        level=level,
        type=f"Test-{level}",
        target_working_time=target_working_time,
        actual_working_time=0,
        forbidden_days=forbidden_days or [],
        forbidden_shifts=[],
        vacation_days=[],
        vacation_shifts=[],
        wish_days=wish_days or [],
        wish_shifts=wish_shifts or [],
        planned_shifts=[],
        qualifications=qualifications or [],
    )


def empty_week_staffing() -> dict[str, dict[str, int]]:
    return {
        "Mo": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Di": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Mi": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Do": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Fr": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "Sa": {"F": 0, "Z": 0, "S": 0, "N": 0},
        "So": {"F": 0, "Z": 0, "S": 0, "N": 0},
    }


def make_two_day_fachkraft_early_fixture() -> CleanSolverFixture:
    """Smallest useful solver fixture that avoids polluted JSON/SQL data."""
    start_date = date(2024, 11, 2)
    days = make_days(start_date, 2)

    fachkraft_staffing = empty_week_staffing()
    fachkraft_staffing["Sa"]["F"] = 1
    fachkraft_staffing["So"]["F"] = 1

    return CleanSolverFixture(
        unit=999,
        start_date=start_date,
        end_date=days[-1],
        days=days,
        shifts=make_standard_shifts(),
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
            "Fachkraft": fachkraft_staffing,
        },
    )


def make_one_week_two_level_reference_fixture() -> CleanSolverFixture:
    """Reference fixture for validating current hard scheduling invariants."""
    start_date = date(2024, 11, 4)
    days = make_days(start_date, 7)

    fachkraft_staffing = empty_week_staffing()
    hilfskraft_staffing = empty_week_staffing()

    for weekday in fachkraft_staffing:
        fachkraft_staffing[weekday]["F"] = 1
        hilfskraft_staffing[weekday]["S"] = 1

    return CleanSolverFixture(
        unit=1000,
        start_date=start_date,
        end_date=days[-1],
        days=days,
        shifts=make_standard_shifts(),
        employees=[
            make_employee(
                key=1,
                name="Alice",
                level="Fachkraft",
                target_working_time=1840,
                forbidden_days=[6],
                qualifications=["rounds"],
            ),
            make_employee(
                key=2,
                name="Bob",
                level="Fachkraft",
                target_working_time=1840,
                wish_days=[10],
                qualifications=["rounds"],
            ),
            make_employee(
                key=3,
                name="Carla",
                level="Hilfskraft",
                target_working_time=1840,
                forbidden_days=[8],
            ),
            make_employee(
                key=4,
                name="David",
                level="Hilfskraft",
                target_working_time=1840,
                wish_shifts=[(9, "S")],
            ),
        ],
        min_staffing={
            "Fachkraft": fachkraft_staffing,
            "Hilfskraft": hilfskraft_staffing,
        },
    )
