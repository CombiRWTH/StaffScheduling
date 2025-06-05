from .loader import Loader
from employee import Employee
from json import load


class FSLoader(Loader):
    _case_id: int

    def __init__(self, case_id: int):
        super().__init__()

        self._case_id = case_id

    def get_employees(self) -> list[Employee]:
        fs_employees = self._load_json("employees")["employees"]
        employees = []
        for fs_employee in fs_employees:
            employees.append(
                Employee(
                    fs_employee["PersNr"],
                    fs_employee["name"],
                    fs_employee["firstname"],
                    fs_employee["type"],
                )
            )
        return employees

    def _load_json(self, filename: str):
        file_path = self._get_file_path(filename)
        with open(file_path, "r") as file:
            return load(file)

    def _get_file_path(self, filename: str) -> str:
        return f"./cases/{self._case_id}/{filename}.json"
