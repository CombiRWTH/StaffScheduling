import logging
import os
import re
from datetime import date, timedelta
from json import dump, load
from os import listdir
from typing import Any

from src.employee import Employee
from src.shift import Shift
from src.solution import Solution

from .loader import Loader


class FSLoader(Loader):
    _case_id: int
    _start_date: date | None
    _end_date: date | None
    _month_folder: str | None

    def __init__(self, case_id: int, start_date: date | None = None, end_date: date | None = None):
        super().__init__()

        self._case_id = case_id
        self._start_date = start_date
        self._end_date = end_date

        # Create month folder string from start_date if provided
        if start_date:
            self._month_folder = f"{start_date.month:02d}_{start_date.year}"
        else:
            # Try to find the latest month folder if no date is provided
            self._month_folder = self._find_latest_month_folder()

    def get_employees(self, start: int = 0) -> list[Employee]:
        fs_employees = self._load_json(self._get_file_path("employees"))["employees"]
        fs_employees_levels = self._load_json(self._get_file_path("employee_types"))
        fs_employees_levels: dict[str, str] = {
            type: level for level, types in fs_employees_levels.items() for type in types
        }
        # example how fs_employees_levels would look like based on case77
        # {
        #   'A-Pflegefachkraft (Krankenpflege) (A-81302-018)': 'Azubi',
        #   'A-Pflegeassistent/in (A-81302-014)': 'Azubi',
        #   'Pflegefachkraft (Krankenpflege) (81302-018)': 'Fachkraft',
        #   'Gesundheits- und Krankenpfleger/in (81302-005)': 'Fachkraft',
        #   'Krankenschwester/-pfleger (81302-008)': 'Fachkraft',
        #   'Altenpfleger/in (82102-002)': 'Fachkraft',
        #   'Krankenpflegehelfer/in (1 jährige A.) (81301-006)': 'Hilfskraft',
        #   'Pflegeassistent/in (81302-014)': 'Hilfskraft',
        #   'Helfer/in - stationäre Krankenpflege (81301-002)': 'Hilfskraft',
        #   'Stationshilfe (81301-018)': 'Hilfskraft',
        #   'Bundesfreiwilligendienst (BFD)': 'Hilfskraft',
        #   'Medizinische/r Fachangestellte/r (81102-004)': 'Hilfskraft'
        # }

        fs_employees_target_working: list[dict[str, Any]] = self._load_json(
            self._get_file_path("target_working_minutes")
        )["employees"]
        fs_employees_target: dict[str, int] = {}
        fs_employees_actual: dict[str, int] = {}
        for fs_employee in fs_employees_target_working:
            if "target" in fs_employee:
                fs_employees_target[fs_employee["key"]] = int(fs_employee["target"])
            if "actual" in fs_employee:
                fs_employees_actual[fs_employee["key"]] = int(fs_employee["actual"])

        fs_employees_vacation: list[dict[str, Any]] = self._load_json(
            self._get_file_path("free_shifts_and_vacation_days")
        )["employees"]

        fs_employees_forbidden_days: dict[str, list[int]] = {}
        fs_employees_forbidden_shifts: dict[str, list[tuple[int, str]]] = {}
        fs_employees_vacation_days: dict[str, list[int]] = {}
        fs_employees_vacation_shifts: dict[str, list[tuple[int, str]]] = {}
        fs_employees_planned_shifts: dict[str, list[tuple[int, str]]] = {}
        fs_employees_hidden_actual: dict[str, int] = {}
        shift_map = {shift.name: shift for shift in self.get_shifts()}
        for fs_employee in fs_employees_vacation:
            if "forbidden_days" in fs_employee:
                fs_employees_forbidden_days[fs_employee["key"]] = fs_employee["forbidden_days"]
            if "vacation_days" in fs_employee:
                fs_employees_vacation_days[fs_employee["key"]] = fs_employee["vacation_days"]
            if "vacation_shifts" in fs_employee:
                fs_employees_vacation_shifts[fs_employee["key"]] = [
                    (x[0], x[1]) for x in fs_employee["vacation_shifts"]
                ]
            if "planned_shifts" in fs_employee:
                fs_employees_planned_shifts[fs_employee["key"]] = [(x[0], x[1]) for x in fs_employee["planned_shifts"]]
                fs_employees_hidden_actual[fs_employee["key"]] = fs_employees_actual.get(fs_employee["key"], 0) - sum(
                    [shift_map[x[1]].duration for x in fs_employee["planned_shifts"] if x[1] in shift_map.keys()]
                )

        fs_employees_wish_days: dict[str, list[int]] = {}
        fs_employees_wish_shifts: dict[str, list[tuple[int, str]]] = {}
        fs_employees_wishes_and_blocked: list[dict[str, Any]] = self._load_json(
            self._get_file_path("wishes_and_blocked")
        )["employees"]
        for fs_employee in fs_employees_wishes_and_blocked:
            if "blocked_days" in fs_employee:
                fs_employees_forbidden_days[fs_employee["key"]].extend(fs_employee["blocked_days"])
            if "blocked_shifts" in fs_employee:
                fs_employees_forbidden_shifts[fs_employee["key"]] = [
                    (x[0], x[1]) for x in fs_employee["blocked_shifts"]
                ]
            if "wish_days" in fs_employee:
                fs_employees_wish_days[fs_employee["key"]] = fs_employee["wish_days"]
            if "wish_shifts" in fs_employee:
                fs_employees_wish_shifts[fs_employee["key"]] = [(x[0], x[1]) for x in fs_employee["wish_shifts"]]

        fs_general_settings = self._load_json(self._get_file_path("general_settings"))
        fs_qualifications = fs_general_settings.get("qualifications", {})

        employees: list[Employee] = []
        for i, fs_employee in enumerate(fs_employees):
            id = fs_employee["key"]
            key = fs_employee.get("key")
            surname = fs_employee["name"]
            firstname = fs_employee["firstname"]
            type = fs_employee["type"]
            level = fs_employees_levels[type]
            qualifications = fs_qualifications.get(f"{key}", [])

            target = fs_employees_target.get(id)
            if target is None:
                target = 0
                logging.debug(f"Target working minutes not found for employee {id}!")

            actual = fs_employees_actual.get(id, 0)
            hidden_actual = fs_employees_hidden_actual.get(id, 0)

            forbidden_days = fs_employees_forbidden_days.get(id, [])
            forbidden_shifts = fs_employees_forbidden_shifts.get(id, [])
            vacation_days = fs_employees_vacation_days.get(id, [])
            vacation_shifts = fs_employees_vacation_shifts.get(id, [])
            wish_days = fs_employees_wish_days.get(id, [])
            wish_shifts = fs_employees_wish_shifts.get(id, [])
            planned_shifts = fs_employees_planned_shifts.get(id, [])
            employees.append(
                Employee(
                    key=key if key is not None else i,
                    surname=surname,
                    name=firstname,
                    level=level,
                    type=type,
                    target_working_time=target,
                    actual_working_time=actual,
                    hidden_actual_working_time=hidden_actual,
                    forbidden_days=forbidden_days,
                    forbidden_shifts=forbidden_shifts,
                    vacation_days=vacation_days,
                    vacation_shifts=vacation_shifts,
                    wish_days=wish_days,
                    wish_shifts=wish_shifts,
                    planned_shifts=planned_shifts,
                    qualifications=qualifications,
                )
            )

        # employees += super().get_employees(len(employees))

        # employees += self.get_hidden_employees({"Azubi":3,"Fachkraft":3,"Hilfskraft":3})

        return employees

    @staticmethod
    def get_hidden_employees(num_hidden_employees_per_level: dict[str, int], start: int = 0):
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

    # shouldnt this be a static function?
    def get_shifts(self) -> list[Shift]:
        base_shifts = [
            Shift(Shift.EARLY, "Früh", 360, 820),
            Shift(Shift.INTERMEDIATE, "Zwischen", 480, 940),
            Shift(Shift.LATE, "Spät", 805, 1265),
            Shift(Shift.NIGHT, "Nacht", 1250, 375),
            Shift(Shift.MANAGEMENT, "Z60", 480, 840),
            Shift(5, "F2_", 360, 820),
            Shift(6, "S2_", 805, 1265),
            Shift(7, "N5", 1250, 375),
        ]
        return base_shifts

    def get_days(self, start_date: date, end_date: date) -> list[date]:
        return [start_date + timedelta(days=i) for i in range(end_date.day - start_date.day + 1)]

    def get_min_staffing(self) -> dict[str, dict[str, dict[str, int]]]:
        fs_min_staffing = self._load_json(self._get_file_path("minimal_number_of_staff"))
        return fs_min_staffing

    def get_solution(self, solution_file_name: str) -> Solution:
        fs_solution = self._load_json(self._get_solutions_path(solution_file_name))
        variables = fs_solution["variables"]
        objective = fs_solution.get("objective", 0)

        return Solution(variables=variables, objective=objective)

    def load_solution_file_names(self) -> list[str]:
        files = listdir("./found_solutions")
        solutions: list[str] = []
        for file in files:
            if file.startswith("solution_") and file.endswith(".json"):
                solutions.append(file[:-5])

        return sorted(solutions)

    def write_solution(self, solution: Solution, solution_name: str):
        data = {
            "variables": solution.variables,
            "objective": solution.objective,
        }
        self._write_json(solution_name, data)

    def _load_json(self, file_path: str) -> dict[str, Any]:
        with open(file_path) as file:
            return load(file)

    def _write_json(self, filename: str, data: dict[str, Any]):
        file_path = self._get_solutions_path(filename)
        if not os.path.exists(os.path.dirname(file_path)):
            os.makedirs(os.path.dirname(file_path))
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, "w") as file:
            dump(data, file, indent=4)

    def _get_file_path(self, filename: str) -> str:
        if self._month_folder:
            return f"./cases/{self._case_id}/{self._month_folder}/{filename}.json"
        else:
            return f"./cases/{self._case_id}/{filename}.json"

    def _get_solutions_path(self, filename: str) -> str:
        return f"./found_solutions/{filename}.json"

    def _find_latest_month_folder(self) -> str | None:
        """Find the latest month folder in the case directory.

        Returns the folder name (e.g., '11_2024') or None if no month folders exist.
        """
        case_path = f"./cases/{self._case_id}"
        if not os.path.exists(case_path):
            logging.warning(f"Case directory not found: {case_path}")
            return None

        # Look for folders matching the pattern MM_YYYY
        month_folders: list[tuple[int, int, str]] = []
        for item in os.listdir(case_path):
            item_path = os.path.join(case_path, item)
            if os.path.isdir(item_path) and re.match(r"^\d{2}_\d{4}$", item):
                # Parse the folder name to extract month and year
                month, year = item.split("_")
                month_folders.append((int(year), int(month), item))

        if not month_folders:
            logging.warning(f"No month folders found in {case_path}. Using fallback to root directory.")
            return None

        # Sort by year and month, return the latest
        month_folders.sort(reverse=True)
        latest_folder: str = month_folders[0][2]
        logging.info(f"Using latest month folder: {latest_folder}")
        return latest_folder
