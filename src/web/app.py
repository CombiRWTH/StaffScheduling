from flask import Flask, render_template, request
from loader import Loader
from employee import Employee
from shift import Shift
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
        start_date = min(
            datetime.strptime(
                match(r"\(\d+, '([\d-]+)', \d+\)", key).group(1), "%Y-%m-%d"
            ).date()
            for key in solution.variables.keys()
            if match(r"\(\d+, '([\d-]+)', \d+\)", key)
        )
        days = self._loader.get_days(start_date)

        return render_template(
            "index.html",
            solution_file_names=solution_file_names,
            selected_solution_file_name=selected_solution_file_name,
            variables=solution.variables,
            employees=self._employees,
            days=days,
            shifts=self._shifts,
        )

    def run(self, debug: bool = False):
        self._app.run(debug=debug, port=5020)
