from employee import Employee
from day import Day
from shift import Shift
from ..constraints import Constraint


class Objective(Constraint):
    _weight: float

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        super().__init__(employees, days, shifts)
        self._weight = weight

    @property
    def weight(self) -> float:
        return self._weight
