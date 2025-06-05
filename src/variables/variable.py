from abc import ABC, abstractmethod
from model import Model


class Variable(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def add_to_model(self, model: Model):
        pass
