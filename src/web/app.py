from flask import Flask, render_template, request
from loader import Loader
from employee import Employee
from shift import Shift
from .analyze_solution import analyze_solution
from re import match
from datetime import datetime
from collections import defaultdict


class App:
    _app: Flask
    _loader: Loader
    _employees: list[Employee]
    _shifts: list[Shift]

    def __init__(self, loader: Loader):
        self._app = Flask(__name__)
        self._app.add_url_rule("/", "index", self.index)

        self._loader = loader
        self._employees = self._loader.get_employees()
        self._shifts = self._loader.get_shifts()

    def index(self):
        solution_file_names = self._loader.load_solution_file_names()
        selected_solution_file_name = request.args.get(
            "solution_file_name", solution_file_names[-1]
        )

        solution = self._loader.get_solution(selected_solution_file_name)
        stats = analyze_solution(solution.variables, self._employees, self._shifts)

        days = [
            datetime.strptime(
                match(r"\(\d+, '([\d-]+)', \d+\)", key).group(1), "%Y-%m-%d"
            ).date()
            for key in solution.variables.keys()
            if match(r"\(\d+, '([\d-]+)', \d+\)", key)
        ]
        start_date = min(days)
        end_date = max(days)
        days = self._loader.get_days(start_date, end_date)

        # fulfilled wishes
        wish_granted_cells = (
            set()
        )  # (employee_id, day) if ANY wish was granted on that day
        granted_shift_wish_colors = defaultdict(
            list
        )  # shift colors for granted wished-off shifts
        violated_shift_wish_keys = set()  # for stats only

        for employee in self._employees:
            e_key = employee.get_key()

            for day in days:
                day_key = f"{day}"
                granted = True  # Assume granted unless we find a violation

                # Check day-off wish
                if day.day in employee.get_wish_days:
                    key = f"({e_key}, '{day_key}')"
                    if key not in solution.variables or solution.variables[key] == 1:
                        granted = False  # assigned on a wished-off day

                # Check all shift-off wishes for this day
                for wish_day, abbr in employee.get_wish_shifts:
                    if day.day != wish_day:
                        continue
                    shift = next(
                        (s for s in self._shifts if s.abbreviation == abbr), None
                    )
                    if not shift:
                        continue
                    key = f"({e_key}, '{day_key}', {shift.get_id()})"
                    if key not in solution.variables:
                        granted = False
                    elif solution.variables[key] == 1:
                        violated_shift_wish_keys.add(key)
                        granted = False
                    elif solution.variables[key] == 0:
                        granted_shift_wish_colors[(e_key, day)].append(shift.color)

                has_day_off_wish = day.day in employee.get_wish_days
                has_shift_off_wish = any(
                    day.day == wd for wd, _ in employee.get_wish_shifts
                )
                if granted and (has_day_off_wish or has_shift_off_wish):
                    wish_granted_cells.add((e_key, day))

        return render_template(
            "index.html",
            solution_file_names=solution_file_names,
            selected_solution_file_name=selected_solution_file_name,
            variables=solution.variables,
            employees=self._employees,
            days=days,
            shifts=self._shifts,
            stats=stats,
            wish_granted_cells=wish_granted_cells,  # Changed from wish_assigned_keys
            granted_shift_wish_colors=granted_shift_wish_colors,  # Added
        )

    def run(self, debug: bool = False):
        self._app.run(debug=debug, port=5020)
