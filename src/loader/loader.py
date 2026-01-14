from abc import ABC, abstractmethod
from datetime import date

from src.employee import Employee
from src.shift import Shift
from src.solution import Solution


class Loader(ABC):
    @abstractmethod
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
        min_staffing = self.get_min_staffing()

        num_hidden_employees_per_level = {
            level: max(sum(shifts.values()) for shifts in days.values()) for level, days in min_staffing.items()
        }

        hidden_employees: list[Employee] = []
        last_id = start
        for level, num in num_hidden_employees_per_level.items():
            for new_id in range(last_id, last_id + num):
                hidden_employees.append(
                    Employee(
                        key=new_id,
                        name="Hidden",
                        surname=f"{level}{new_id}",
                        level=level,
                        type="hidden",
                    )
                )
            last_id += num

        return hidden_employees

    @abstractmethod
    def get_shifts(self) -> list[Shift]:
        """
        Retrieves a list of shifts.
        """
        pass

    @abstractmethod
    def get_days(self, start_date: date, end_date: date) -> list[date]:
        pass

    @abstractmethod
    def get_min_staffing(self) -> dict[str, dict[str, dict[str, int]]]:
        """
        Retrieves the minimum staffing requirements.
        """
        pass

    @abstractmethod
    def get_solution(self, solution_file_name: str) -> Solution:
        pass

    @abstractmethod
    def load_solution_file_names(self) -> list[str]:
        pass

    @abstractmethod
    def write_solution(self, solution: Solution, solution_name: str):
        """
        Writes the solution back to the source.
        """
        pass
