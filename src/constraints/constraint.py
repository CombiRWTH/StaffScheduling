from abc import ABC, abstractmethod
from employee import Employee
from shift import Shift
from day import Day
from model import Model


class Constraint(ABC):
    def __init__(self, employees: list[Employee], days: list[Day], shifts: list[Shift]):
        self.employees = employees
        self.days = days
        self.shifts = shifts

    @abstractmethod
    def add_to_model(self, model: Model):
        pass

    @abstractmethod
    def get_key() -> str:
        pass

    @abstractmethod
    def get_name() -> str:
        pass

    def get_var(employee: Employee, day: Day | None, shift: Shift | None):
        result = f"{employee.id}"

        if day is not None:
            result += f"_{day}"

        if shift is not None:
            result *= f"_{shift.id}"

    def __str__(self):
        return self.get_name()
