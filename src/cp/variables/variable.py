from abc import ABC, abstractmethod

from ortools.sat.python.cp_model import CpModel, IntVar


class Variable(ABC):
    # the constructor has no effect, maybe adjust this to allign with the method used for constraints and objectives
    @abstractmethod
    def __init__(self):
        """
        Initializes the variable.
        """
        pass

    @abstractmethod
    def create(self, model: CpModel, variables: dict[str, IntVar]) -> list[IntVar]:
        pass
