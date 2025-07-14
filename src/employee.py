from shift import Shift
from day import Day


class Employee:
    _key: int
    _surname: str
    _name: str
    _level: str
    _type: str
    _target_working_time: int
    _actual_working_time: int = 0
    _forbidden_days: list[int]
    _forbidden_shifts: list[tuple[int, str]]
    _vacation_days: list[int]
    _vacation_shifts: list[tuple[int, str]]
    _wish_days: list[int]
    _wish_shifts: list[tuple[int, str]]
    _planned_shifts: list[tuple[int, str]] = []
    _qualifications: list[str]

    def __init__(
        self,
        key: int,
        surname: str,
        name: str,
        level: str,
        type: str,
        target_working_time: int = 0,
        actual_working_time: int = 0,
        forbidden_days: list[int] = [],
        forbidden_shifts: list[tuple[int, str]] = [],
        vacation_days: list[int] = [],
        vacation_shifts: list[int] = [],
        wish_days: list[int] = [],
        wish_shifts: list[tuple[int, str]] = [],
        planned_shifts: list[tuple[int, str]] = [],
        qualifications: list[str] = [],
    ):
        """
        Initializes an Employee instance.
        """
        self._key = key
        self._surname = surname
        self._name = name
        self._level = level
        self._type = type
        self._target_working_time = target_working_time
        self._actual_working_time = actual_working_time
        self._forbidden_days = forbidden_days
        self._forbidden_shifts = forbidden_shifts
        self._vacation_days = vacation_days
        self._vacation_shifts = vacation_shifts
        self._wish_days = wish_days
        self._wish_shifts = wish_shifts
        self._planned_shifts = planned_shifts or []
        self._qualifications = qualifications

    def get_key(self) -> int:
        return self._key

    @property
    def level(self) -> str:
        return self._level

    @property
    def hidden(self) -> bool:
        return self._type == "hidden"

    @property
    def name(self) -> str:
        return f"{self._surname} {self._name}"

    def qualified(self, qualification: str) -> bool:
        """
        Checks if the employee has a specific qualification.
        """
        return qualification in self._qualifications

    def get_available_working_time(self) -> int:
        """
        Calculates the target working time for the employee.
        """
        return max(self._target_working_time - self._actual_working_time, 0)

    def unavailable(self, day: Day, shift: Shift = None) -> bool:
        """
        Checks if the employee has vacation or is not available on a specific day and optionally a specific shift.
        If `shift` is None, it checks if the employee has vacation on that day regardless of the shift.
        """
        if shift is None:
            return day.day in self._vacation_days or day.day in self._forbidden_days

        return (day.day, shift.abbreviation) in self._vacation_shifts or (
            day.day,
            shift.abbreviation,
        ) in self._forbidden_shifts

    @property
    def get_wish_days(self) -> list[int]:
        return self._wish_days

    @property
    def get_wish_shifts(self) -> list[tuple[int, str]]:
        return self._wish_shifts
