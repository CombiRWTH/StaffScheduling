from abc import ABC, abstractmethod
from employee import Employee
from day import Day
from shift import Shift
from ..variables import Variable
from ortools.sat.python.cp_model import CpModel


class Constraint(ABC):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        """
        Initializes the constraint with the given employees, days, and shifts.
        """
        self._employees = employees
        self._days = days
        self._shifts = shifts

    @property
    @abstractmethod
    def KEY(cls) -> str:
        raise NotImplementedError

    @abstractmethod
    def create(self, model: CpModel, variables: dict[str, Variable]):
        """
        Creates the constraint in the given CP model using the provided variables.
        """
        pass

    @property
    def name(self) -> str:
        return self.KEY.replace("-", " ").title()
