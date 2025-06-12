from abc import ABC, abstractmethod
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable
from ortools.sat.python.cp_model import CpModel


class Constraint(ABC):
    _key: str

    def __init__(
        self, key: str, employees: list[Employee], days: list[Day], shifts: list[Shift]
    ):
        self._key = key

        self._employees = employees
        self._days = days
        self._shifts = shifts

    @abstractmethod
    def create(self, model: CpModel, variables: dict[str, Variable]):
        pass

    @property
    def name(self) -> str:
        return self._key.replace("-", " ").title()
