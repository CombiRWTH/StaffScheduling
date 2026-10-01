from collections import defaultdict
from datetime import date, datetime
from re import match

from flask import Flask, render_template, request

from ..employee import Employee
from ..loader import Loader
from ..shift import Shift
from .analyze_solution import analyze_solution


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
        selected_solution_file_name = request.args.get("solution_file_name", solution_file_names[-1])

        solution = self._loader.get_solution(selected_solution_file_name)
        stats = analyze_solution(solution.variables, self._employees, self._shifts)

        days = [
            datetime.strptime(m.group(1), "%Y-%m-%d").date()
            for key in solution.variables.keys()
            if (m := match(r"\(\d+, '([\d-]+)', \d+\)", key)) is not None
        ]
        start_date = min(days)
        end_date = max(days)
        days = self._loader.get_days(start_date, end_date)

        # fulfilled wishes
        fulfilled_shift_wish_cells: set[tuple[int, date]] = set()
        fulfilled_day_off_cells: set[tuple[int, date]] = set()
        all_shift_wish_colors: defaultdict[tuple[int, date], list[str]] = defaultdict(list)
        all_day_off_wish_cells: set[tuple[int, date]] = set()

        for employee in self._employees:
            e_key = employee.get_key()

            for day in days:
                day_key = f"{day}"
                cell_key = (e_key, day)

                # --- DAY OFF WISHES ---
                if day.day in employee.get_wish_days:
                    all_day_off_wish_cells.add(cell_key)

                    # Now: check if ANY shift is assigned on that day
                    shift_assigned = any(
                        solution.variables.get(f"({e_key}, '{day_key}', {shift.get_id()})") == 1
                        for shift in self._shifts
                        if not shift.is_exclusive
                    )

                    if not shift_assigned:
                        fulfilled_day_off_cells.add(cell_key)

                # --- SHIFT OFF WISHES ---
                shift_wishes = [
                    s
                    for wd, abbr in employee.get_wish_shifts
                    if wd == day.day
                    for s in self._shifts
                    if s.abbreviation == abbr
                ]

                if shift_wishes:
                    all_shift_wish_colors[cell_key] += [s.color for s in shift_wishes]

                    # fulfilled only if NONE of the wished shifts are assigned
                    fulfilled = True
                    for shift in shift_wishes:
                        key = f"({e_key}, '{day_key}', {shift.get_id()})"
                        if solution.variables.get(key) == 1:
                            fulfilled = False
                            break
                    if fulfilled and day.day not in employee.get_wish_days:
                        fulfilled_shift_wish_cells.add(cell_key)

        return render_template(
            "index.html",
            solution_file_names=solution_file_names,
            selected_solution_file_name=selected_solution_file_name,
            variables=solution.variables,
            employees=self._employees,
            days=days,
            shifts=self._shifts,
            stats=stats,
            fulfilled_shift_wish_cells=fulfilled_shift_wish_cells,
            fulfilled_day_off_cells=fulfilled_day_off_cells,
            all_shift_wish_colors=all_shift_wish_colors,
            all_day_off_wish_cells=all_day_off_wish_cells,
        )

    def run(self, debug: bool = False):
        self._app.run(debug=debug, port=5020)
