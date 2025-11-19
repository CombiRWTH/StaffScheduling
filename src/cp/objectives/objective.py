from abc import abstractmethod

from ortools.sat.python.cp_model import CpModel, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..constraints import Constraint
from ..variables import Variable


class Objective(Constraint):
    _weight: float

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the objective with a weight and the given employees, days, and shifts.
        """
        super().__init__(employees, days, shifts)
        self._weight = weight

    @property
    def weight(self) -> float:
        return self._weight

    @abstractmethod
    def create(self, model: CpModel, variables: dict[str, Variable]) -> LinearExpr | None:
        """
        Creates the objective penalty terms in the given CP model.

        Returns a LinearExpr representing the penalty to be minimized, or None if no penalty applies.
        """
        pass
