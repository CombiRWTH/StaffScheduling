from shift import Shift


class Employee:
    _id: str
    _surname: str
    _name: str
    _type: str
    _level: str
    _target_working_time: int
    _vacation_days: list[int]
    _vacation_shifts: list[tuple[int, str]]

    def __init__(
        self,
        id: str,
        surname: str,
        name: str,
        type: str,
        level: str,
        target_working_time: int,
        vacation_days: list[int] = [],
        vacation_shifts: list[int] = [],
    ):
        self._id = id
        self._surname = surname
        self._name = name
        self._type = type
        self._level = level
        self._target_working_time = target_working_time
        self._vacation_days = vacation_days
        self._vacation_shifts = vacation_shifts

    def get_id(self) -> str:
        return self._id

    @property
    def level(self) -> str:
        return self._level

    def get_target_working_time(
        self, shifts: list[Shift] = [], subtract_vacation: bool = True
    ) -> int:
        if subtract_vacation:
            if shifts == []:
                raise ValueError(
                    "Shifts must be provided to calculate target working time with vacation subtracted."
                )

            vacation_time = len(self._vacation_days) * min(
                shift.duration for shift in shifts
            )

            return self._target_working_time - vacation_time

        return self._target_working_time

    def has_vacation(self, day: int, shift: int = None) -> bool:
        if shift is None:
            return day in self._vacation_days

        shift_abbreviations = {0: "F", 1: "S", 2: "N"}
        return (day, shift_abbreviations[shift]) in self._vacation_shifts
