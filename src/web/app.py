from flask import Flask, render_template, request
from loader import FSLoader, Loader
from datetime import date
from employee import Employee
from day import Day
from shift import Shift
from .analyze_solution import analyze_solution


class App:
    _app: Flask
    _loader: Loader
    _employees: list[Employee]
    _days: list[Day]
    _shifts: list[Shift]

    def __init__(self, case_id: int, start_date: date):
        self._app = Flask(__name__)
        self._app.add_url_rule("/", "index", self.index)

        self._loader = FSLoader(case_id)
        self._employees = self._loader.get_employees()
        self._days = self._loader.get_days(start_date)
        self._shifts = self._loader.get_shifts()

    def index(self):
        solution_file_names = self._loader.load_solution_file_names()
        selected_solution_file_name = request.args.get(
            "solution_file_name", solution_file_names[-1]
        )

        solution = self._loader.get_solution(selected_solution_file_name)
        stats = analyze_solution(solution.variables, self._employees, self._shifts)

        return render_template(
            "index.html",
            solution_file_names=solution_file_names,
            selected_solution_file_name=selected_solution_file_name,
            variables=solution.variables,
            employees=self._employees,
            days=self._days,
            shifts=self._shifts,
            stats=stats,
        )

    def run(self):
        self._app.run(debug=True, port=5020)
