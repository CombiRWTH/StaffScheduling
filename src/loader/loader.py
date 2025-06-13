from abc import ABC, abstractmethod
from employee import Employee
from shift import Shift
from solution import Solution


class Loader(ABC):
    @abstractmethod
    def get_employees() -> list[Employee]:
        pass

    @abstractmethod
    def get_shifts(self) -> list[Shift]:
        pass

    @abstractmethod
    def get_min_staffing(self) -> dict[str, dict[str, dict[dict[str, int]]]]:
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
        pass
