from abc import ABC, abstractmethod
from employee import Employee
from ortools.sat.python import cp_model

class Constraint(ABC):
    def __init__(self, name: str, employees: list[Employee], days: int, shifts: int):
        self.name = name
        self.employees = employees
        self.days = days
        self.shifts = shifts

    @abstractmethod
    def add_to_model(model: cp_model.CpModel):
        pass

    def __str__(self):
        return self.name;