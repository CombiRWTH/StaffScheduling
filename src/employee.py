from shift import Shift


class Employee:
    _id: str
    _surname: str
    _name: str
    _type: str
    _target_working_time: int
    _vacation_days: list[int]
    _vacation_shifts: list[int]

    def __init__(
        self,
        id: str,
        surname: str,
        name: str,
        type: str,
        target_working_time: int,
        vacation_days: list[int] = [],
        vacation_shifts: list[int] = [],
    ):
        self._id = id
        self._surname = surname
        self._name = name
        self._type = type
        self._target_working_time = target_working_time
        self._vacation_days = vacation_days
        self._vacation_shifts = vacation_shifts

    def get_id(self) -> str:
        return self._id

    def get_target_working_time(
        self, shifts: list[Shift] = [], subtract_vacation: bool = True
    ) -> int:
        if subtract_vacation:
            if shifts == []:
                raise ValueError(
                    "Shifts must be provided to calculate target working time with vacation subtracted."
                )

            vacation_time = 0
            vacation_time += len(self._vacation_days) * min(
                shift.get_duration() for shift in shifts
            )

            return self._target_working_time - vacation_time

        return self._target_working_time
