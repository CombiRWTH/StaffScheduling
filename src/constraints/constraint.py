from abc import ABC, abstractmethod
from variables.variable import Variable
from ortools.sat.python.cp_model import CpModel


class Constraint(ABC):
    def __init__(self, key: str):
        self._key = key

    @abstractmethod
    def create(self, model: CpModel, variables: dict[str, Variable]):
        pass
