from abc import abstractmethod
from employee import Employee
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel


class Objective:
    _key: str
    _weight: float
    _employees: list[Employee]
    _days: list[Day]
    _shifts: list[Shift]

    def __init__(
        self,
        key: str,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        self._key = key
        self._weight = weight
        self._employees = employees
        self._days = days
        self._shifts = shifts

    @abstractmethod
    def create(self, model: CpModel):
        pass
