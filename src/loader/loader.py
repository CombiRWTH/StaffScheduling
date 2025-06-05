from abc import ABC, abstractmethod
from employee import Employee


class Loader(ABC):
    @abstractmethod
    def get_employees() -> list[Employee]:
        pass
