from flask import Flask, render_template, request
from loader import Loader
from employee import Employee
from shift import Shift
from .analyze_solution import analyze_solution
from re import match
from datetime import datetime


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
        wish_assigned_keys = set()
        for employee in self._employees:
            for wish_day, abbr in employee.get_wish_shifts:
                for day in days:
                    if day.day == wish_day:
                        shift = next(
                            (s for s in self._shifts if s.abbreviation == abbr), None
                        )
                        if not shift:
                            continue
                        key = f"({employee.get_key()}, '{day}', {shift.get_id()})"
                        if solution.variables.get(key) == 1:
                            wish_assigned_keys.add(key)

        return render_template(
            "index.html",
            solution_file_names=solution_file_names,
            selected_solution_file_name=selected_solution_file_name,
            variables=solution.variables,
            employees=self._employees,
            days=days,
            shifts=self._shifts,
            stats=stats,
            wish_assigned_keys=wish_assigned_keys,
        )

    def run(self, debug: bool = False):
        self._app.run(debug=debug, port=5020)
