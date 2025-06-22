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
    def get_employees(self, start: int = 0) -> list[Employee]:
        """
        Retrieves a list of employees.
        """
        return [
            Employee(
                id=start, name="Hidden", surname="Azubi0", level="Azubi", type="hidden"
            ),
            Employee(
                id=start + 1,
                name="Hidden",
                surname="Fachkraft0",
                level="Fachkraft",
                type="hidden",
            ),
            Employee(
                id=start + 2,
                name="Hidden",
                surname="Fachkraft1",
                level="Fachkraft",
                type="hidden",
            ),
            Employee(
                id=start + 3,
                name="Hidden",
                surname="Fachkraft2",
                level="Fachkraft",
                type="hidden",
            ),
            Employee(
                id=start + 4,
                name="Hidden",
                surname="Fachkraft3",
                level="Fachkraft",
                type="hidden",
            ),
            Employee(
                id=start + 5,
                name="Hidden",
                surname="Hilfskraft0",
                level="Hilfskraft",
                type="hidden",
            ),
            Employee(
                id=start + 6,
                name="Hidden",
                surname="Hilfskraft1",
                level="Hilfskraft",
                type="hidden",
            ),
        ]

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
