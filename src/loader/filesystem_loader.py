from .loader import Loader
from employee import Employee
from shift import Shift
from solution import Solution
from json import load, dump
from datetime import datetime
import logging
from os import listdir
from datetime import date
from datetime import timedelta
from calendar import monthrange


class FSLoader(Loader):
    _case_id: int

    def __init__(self, case_id: int):
        super().__init__()

        self._case_id = case_id

    def get_employees(self) -> list[Employee]:
        fs_employees = self._load_json(self._get_file_path("employees"))["employees"]
        fs_employees_levels = self._load_json(self._get_file_path("employee_types"))
        fs_employees_levels: dict = {
            type: level
            for level, types in fs_employees_levels.items()
            for type in types
        }

        fs_employees_target_working: list = self._load_json(
            self._get_file_path("target_working_minutes")
        )["employees"]
        fs_employees_target: dict = {}
        fs_employees_actual: dict = {}

        for fs_employee in fs_employees_target_working:
            if "target" in fs_employee:
                fs_employees_target[fs_employee["PersNr"]] = fs_employee["target"]
            if "actual" in fs_employee:
                fs_employees_actual[fs_employee["PersNr"]] = fs_employee["actual"]

        fs_employees_vacation: list = self._load_json(
            self._get_file_path("free_shifts_and_vacation_days")
        )["employees"]
        fs_employees_forbidden_days: dict = {}
        fs_employees_forbidden_shifts: dict = {}
        fs_employees_vacation_days: dict = {}
        fs_employees_vacation_shifts: dict = {}
        fs_employees_wish_days: dict = {}
        fs_employees_wish_shifts: dict = {}

        for fs_employee in fs_employees_vacation:
            if "forbidden_days" in fs_employee:
                fs_employees_forbidden_days[fs_employee["PersNr"]] = fs_employee[
                    "forbidden_days"
                ]
            if "forbidden_shifts" in fs_employee:
                fs_employees_forbidden_shifts[fs_employee["PersNr"]] = list(
                    map(lambda x: (x[0], x[1]), fs_employee["forbidden_shifts"])
                )
            if "vacation_days" in fs_employee:
                fs_employees_vacation_days[fs_employee["PersNr"]] = fs_employee[
                    "vacation_days"
                ]
            if "vacation_shifts" in fs_employee:
                fs_employees_vacation_shifts[fs_employee["PersNr"]] = list(
                    map(lambda x: (x[0], x[1]), fs_employee["vacation_shifts"])
                )
            if "wish_days" in fs_employee:
                fs_employees_wish_days[fs_employee["PersNr"]] = fs_employee["wish_days"]
            if "wish_shifts" in fs_employee:
                fs_employees_wish_shifts[fs_employee["PersNr"]] = list(
                    map(lambda x: (x[0], x[1]), fs_employee["wish_shifts"])
                )

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

            actual = fs_employees_actual.get(id, 0)

            forbidden_days = fs_employees_forbidden_days.get(id, [])
            forbidden_shifts = fs_employees_forbidden_shifts.get(id, [])
            vacation_days = fs_employees_vacation_days.get(id, [])
            vacation_shifts = fs_employees_vacation_shifts.get(id, [])
            wish_days = fs_employees_wish_days.get(id, [])
            wish_shifts = fs_employees_wish_shifts.get(id, [])

            employees.append(
                Employee(
                    id=i,
                    surname=surname,
                    name=firstname,
                    type=type,
                    level=level,
                    target_working_time=target,
                    actual_working_time=actual,
                    forbidden_days=forbidden_days,
                    forbidden_shifts=forbidden_shifts,
                    vacation_days=vacation_days,
                    vacation_shifts=vacation_shifts,
                    wish_days=wish_days,
                    wish_shifts=wish_shifts,
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

    def get_days(self, start_date: date) -> list[date]:
        return [
            start_date + timedelta(days=i)
            for i in range(monthrange(start_date.year, start_date.month)[1])
        ]

    def get_min_staffing(self) -> dict[str, dict[str, dict[dict[str, int]]]]:
        fs_min_staffing = self._load_json(
            self._get_file_path("minimal_number_of_staff")
        )
        return fs_min_staffing

    def get_solution(self, solution_file_name: str) -> Solution:
        fs_solution = self._load_json(self._get_solutions_path(solution_file_name))
        variables = fs_solution["variables"]
        objective = fs_solution.get("objective", 0)

        return Solution(variables=variables, objective=objective)

    def load_solution_file_names(self) -> list[str]:
        files = listdir("./found_solutions")
        solutions = []
        for file in files:
            if file.startswith("solutions_") and file.endswith(".json"):
                solutions.append(file[:-5])

        return sorted(solutions)

    def write_solution(
        self,
        solution: Solution,
    ):
        data = {
            "variables": solution.variables,
            "objective": solution.objective,
        }
        self._write_json(
            f"solutions_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}", data
        )

    def _load_json(self, file_path: str) -> dict:
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
