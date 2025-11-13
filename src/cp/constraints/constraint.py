from abc import ABC, abstractmethod

from ortools.sat.python.cp_model import CpModel, LinearExpr

from day import Day
from employee import Employee
from shift import Shift

from ..variables import Variable


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
    def create(self, model: CpModel, variables: dict[str, Variable]) -> LinearExpr | None:
        """
        Creates the constraint or objective in the given CP model using the provided variables.

        For hard constraints, this method should return None after adding constraints to the model.
        For objectives (soft constraints), this method should return a LinearExpr representing
        the penalty term to be minimized.
        """
        pass

    @property
    def name(self) -> str:
        return self.KEY.replace("-", " ").title()
