from abc import ABC, abstractmethod
from ortools.sat.python.cp_model import CpModel, IntVar


class Variable(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create(self, model: CpModel) -> list[IntVar]:
        pass
