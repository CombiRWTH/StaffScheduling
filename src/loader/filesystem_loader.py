from .loader import Loader
from employee import Employee
from shift import Shift
from json import load


class FSLoader(Loader):
    _case_id: int

    def __init__(self, case_id: int):
        super().__init__()

        self._case_id = case_id

    def get_employees(self) -> list[Employee]:
        fs_employees = self._load_json("employees")["employees"]
        fs_employees_target: list = self._load_json("target_working_minutes")[
            "employees"
        ]
        fs_employees_target: dict = {
            fs_employee["PersNr"]: fs_employee["target"]
            for fs_employee in fs_employees_target
        }

        employees = []
        for fs_employee in fs_employees:
            id = fs_employee["PersNr"]
            surname = fs_employee["name"]
            firstname = fs_employee["firstname"]
            type = fs_employee["type"]

            target = fs_employees_target[id]
            if target is None:
                raise ValueError(f"Target working minutes not found for employee {id}!")

            employees.append(Employee(id, surname, firstname, type, target))

        return employees

    def get_shifts(self) -> list[Shift]:
        return [Shift(1, "Früh", 460), Shift(2, "Spät", 460), Shift(3, "Nacht", 565)]

    def _load_json(self, filename: str):
        file_path = self._get_file_path(filename)
        with open(file_path, "r") as file:
            return load(file)

    def _get_file_path(self, filename: str) -> str:
        return f"./cases/{self._case_id}/{filename}.json"
