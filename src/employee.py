from shift import Shift
from day import Day


class Employee:
    _id: str
    _surname: str
    _name: str
    _type: str
    _level: str
    _target_working_time: int
    _actual_working_time: int = 0
    _forbidden_days: list[int]
    _forbidden_shifts: list[tuple[int, str]]
    _vacation_days: list[int]
    _vacation_shifts: list[tuple[int, str]]
    _wish_days: list[int]
    _wish_shifts: list[tuple[int, str]]

    def __init__(
        self,
        id: str,
        surname: str,
        name: str,
        type: str,
        level: str,
        target_working_time: int = 0,
        actual_working_time: int = 0,
        forbidden_days: list[int] = [],
        forbidden_shifts: list[tuple[int, str]] = [],
        vacation_days: list[int] = [],
        vacation_shifts: list[int] = [],
        wish_days: list[int] = [],
        wish_shifts: list[tuple[int, str]] = [],
    ):
        """
        Initializes an Employee instance.
        """
        self._id = id
        self._surname = surname
        self._name = name
        self._type = type
        self._level = level
        self._target_working_time = target_working_time
        self._actual_working_time = actual_working_time
        self._forbidden_days = forbidden_days
        self._forbidden_shifts = forbidden_shifts
        self._vacation_days = vacation_days
        self._vacation_shifts = vacation_shifts
        self._wish_days = wish_days
        self._wish_shifts = wish_shifts

    def get_id(self) -> str:
        return self._id

    @property
    def level(self) -> str:
        return self._level

    @property
    def name(self) -> str:
        return f"{self._surname} {self._name}"

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
