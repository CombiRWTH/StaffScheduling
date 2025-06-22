from abc import ABC, abstractmethod
from employee import Employee
from shift import Shift
from solution import Solution


class Loader(ABC):
    def __init__(self):
        """
        Initializes the loader.
        """
        pass

    @abstractmethod
    def get_employees(self) -> list[Employee]:
        """
        Retrieves a list of employees.
        """
        pass

    @abstractmethod
    def get_shifts(self) -> list[Shift]:
        """
        Retrieves a list of shifts.
        """
        pass

    @abstractmethod
    def get_min_staffing(self) -> dict[str, dict[str, dict[dict[str, int]]]]:
        """
        Retrieves the minimum staffing requirements.
        """
        pass

    @abstractmethod
    def write_solutions(
        self,
        case: int,
        employees: list[Employee],
        constraints: list[str],
        shifts: list[Shift],
        solutions: list[Solution],
    ):
        """
        Writes the solution back to the source.
        """
        pass
