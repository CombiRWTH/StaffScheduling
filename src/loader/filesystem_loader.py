from .loader import Loader
from employee import Employee
from shift import Shift
from solution import Solution
from json import load, dump
from datetime import datetime
import logging


class FSLoader(Loader):
    _case_id: int

    def __init__(self, case_id: int):
        super().__init__()

        self._case_id = case_id

    def get_employees(self) -> list[Employee]:
        fs_employees = self._load_json("employees")["employees"]
        fs_employees_levels = self._load_json("employee_types")
        fs_employees_levels: dict = {
            type: level
            for level, types in fs_employees_levels.items()
            for type in types
        }

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
            fs_employee["PersNr"]: list(
                map(lambda x: (x[0], x[1]), fs_employee["free_shifts"])
            )
            for fs_employee in fs_employees_vacation
        }

        employees = []
        for i, fs_employee in enumerate(fs_employees):
            id = fs_employee["PersNr"]
            surname = fs_employee["name"]
            firstname = fs_employee["firstname"]
            type = fs_employee["type"]
            level = fs_employees_levels[type]

            target = fs_employees_target.get(id)
            if target is None:
                target = 0
                logging.debug(f"Target working minutes not found for employee {id}!")

            vacation_days = fs_employees_vacation_days.get(id)
            if vacation_days is None:
                vacation_days = []
                logging.debug(f"Vacation days not found for employee {id}!")

            vacation_shifts = fs_employees_vacation_shifts.get(id)
            if vacation_shifts is None:
                vacation_shifts = []
                logging.debug(f"Vacation shifts not found for employee {id}!")

            employees.append(
                Employee(
                    id=i,
                    surname=surname,
                    name=firstname,
                    type=type,
                    level=level,
                    target_working_time=target,
                    vacation_days=vacation_days,
                    vacation_shifts=vacation_shifts,
                )
            )

        return employees

    def get_shifts(self) -> list[Shift]:
        """
        Actual shifts from timeoffice:
        return [
            Shift(1, "Früh", 360, 850),
            Shift(2, "Spät", 770, 1260),
            Shift(3, "Nacht", 1220, 390),
        ]
        """
        return [
            Shift(Shift.EARLY, "Früh", 360, 820),
            Shift(Shift.LATE, "Spät", 805, 1265),
            Shift(Shift.NIGHT, "Nacht", 1250, 375),
        ]

    def get_min_staffing(self) -> dict[str, dict[str, dict[dict[str, int]]]]:
        fs_min_staffing = self._load_json("minimal_number_of_staff")
        return fs_min_staffing

    def write_solutions(
        self,
        case: int,
        employees: list[Employee],
        constraints: list[str],
        shifts: list[Shift],
        solutions: list[Solution],
    ):
        data = {
            "case_id": case,
            "employees": {
                "name_to_index": {
                    employee._surname: int(employee.get_id()) for employee in employees
                },
                "name_to_target": {
                    employee._surname: employee.get_target_working_time(shifts)
                    for employee in employees
                },
            },
            "constraints": constraints,
            "num_of_solutions": len(solutions),
            "givenSolutionLimit": len(solutions),
            "shiftDurations": {shift._name[0]: shift.duration for shift in shifts},
            "solutions": [solution.variables for solution in solutions],
        }
        self._write_json(
            f"solutions_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}", data
        )

    def _load_json(self, filename: str):
        file_path = self._get_file_path(filename)
        with open(file_path, "r") as file:
            return load(file)

    def _write_json(self, filename: str, data: dict):
        file_path = self._get_solutions_path(filename)
        with open(file_path, "w") as file:
            dump(data, file, indent=4)

    def _get_file_path(self, filename: str) -> str:
        return f"./cases/{self._case_id}/{filename}.json"

    def _get_solutions_path(self, filename: str) -> str:
        return f"./found_solutions/{filename}.json"
