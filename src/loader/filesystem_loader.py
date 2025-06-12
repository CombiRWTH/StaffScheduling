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
        fs_employees_vacation: list = self._load_json("free_shifts_and_vacation_days")[
            "employees"
        ]
        fs_employees_vacation_days: dict = {
            fs_employee["PersNr"]: fs_employee["free_days"]
            for fs_employee in fs_employees_vacation
        }
        fs_employees_vacation_shifts: dict = {
            fs_employee["PersNr"]: fs_employee["free_shifts"]
            for fs_employee in fs_employees_vacation
        }

        employees = []
        for fs_employee in fs_employees:
            id = fs_employee["PersNr"]
            surname = fs_employee["name"]
            firstname = fs_employee["firstname"]
            type = fs_employee["type"]

            target = fs_employees_target.get(id)
            if target is None:
                target = 0
                print(f"Target working minutes not found for employee {id}!")

            vacation_days = fs_employees_vacation_days.get(id)
            if vacation_days is None:
                vacation_days = []
                print(f"Vacation days not found for employee {id}!")

            vacation_shifts = fs_employees_vacation_shifts.get(id)
            if vacation_shifts is None:
                vacation_shifts = []
                print(f"Vacation shifts not found for employee {id}!")

            employees.append(
                Employee(
                    id, surname, firstname, type, target, vacation_days, vacation_shifts
                )
            )

        return employees

    def get_shifts(self) -> list[Shift]:
        return [Shift(1, "Früh", 460), Shift(2, "Spät", 460), Shift(3, "Nacht", 565)]

    def _load_json(self, filename: str):
        file_path = self._get_file_path(filename)
        with open(file_path, "r") as file:
            return load(file)

    def _get_file_path(self, filename: str) -> str:
        return f"./cases/{self._case_id}/{filename}.json"
