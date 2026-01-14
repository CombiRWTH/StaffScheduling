import json
import os
from collections import defaultdict
from datetime import date, datetime
from re import match

from ..employee import Employee
from ..loader import Loader
from ..shift import Shift
from ..solution import Solution
from .analyze_solution import analyze_solution


def employee_to_dict(emp: Employee):
    return {
        "id": emp.get_key(),
        "name": emp.name,
        "level": emp.level,
        "target_working_time": emp.target_working_time,
        "wishes": {
            "shift_wishes": [[day, shift] for (day, shift) in emp.get_wish_shifts],
            "day_off_wishes": list(emp.get_wish_days),
        },
        "forbidden_days": emp._forbidden_days,  # type: ignore
        "forbidden_shifts": emp._forbidden_shifts,  # type: ignore
        "vacation_days": emp.vacation_days,
        "vacation_shifts": emp.vacation_shifts,
        "hidden_actual_working_time": emp._hidden_actual_working_time 
    }


def shift_to_dict(shift: Shift):
    return {
        "id": shift.get_id(),
        "name": shift.name,
        "abbreviation": shift.abbreviation,
        "color": shift.color,
        "duration": shift.duration,
        "is_exclusive": shift.is_exclusive,
    }


def collect_day_information(solution: Solution, employees: list[Employee], shifts: list[Shift], loader: Loader):
    # Extract dates from variable keys
    days_raw = [
        datetime.strptime(m.group(1), "%Y-%m-%d").date()
        for key in solution.variables.keys()
        if (m := match(r"\(\d+, '([\d-]+)', \d+\)", key)) is not None
    ]

    start_date = min(days_raw)
    end_date = max(days_raw)
    days = loader.get_days(start_date, end_date)

    fulfilled_shift_wish_cells: set[tuple[int, date]] = set()
    fulfilled_day_off_cells: set[tuple[int, date]] = set()
    all_shift_wish_colors: defaultdict[tuple[int, date], list[str]] = defaultdict(list)
    all_day_off_wish_cells: set[tuple[int, date]] = set()

    for employee in employees:
        e_key = employee.get_key()

        for day in days:
            day_key = f"{day}"
            cell_key = (e_key, day)

            # --- DAY OFF WISHES ---
            if day.day in employee.get_wish_days:
                all_day_off_wish_cells.add(cell_key)

                shift_assigned = any(
                    solution.variables.get(f"({e_key}, '{day_key}', {shift.get_id()})") == 1
                    for shift in shifts
                    if not shift.is_exclusive
                )

                if not shift_assigned:
                    fulfilled_day_off_cells.add(cell_key)

            # --- SHIFT WISHES ---
            shift_wishes = [
                s for wd, abbr in employee.get_wish_shifts if wd == day.day for s in shifts if s.abbreviation == abbr
            ]

            if shift_wishes:
                all_shift_wish_colors[cell_key] += [s.color for s in shift_wishes]

                fulfilled = True
                for shift in shift_wishes:
                    key = f"({e_key}, '{day_key}', {shift.get_id()})"
                    if solution.variables.get(key) == 1:
                        fulfilled = False
                        break

                if fulfilled and day.day not in employee.get_wish_days:
                    fulfilled_shift_wish_cells.add(cell_key)

    return {
        "days": days,
        "fulfilled_shift_wish_cells": list(fulfilled_shift_wish_cells),
        "fulfilled_day_off_cells": list(fulfilled_day_off_cells),
        "all_shift_wish_colors": {f"{k[0]}-{k[1].isoformat()}": v for k, v in all_shift_wish_colors.items()},
        "all_day_off_wish_cells": list(all_day_off_wish_cells),
    }


def process_solution(
    loader: Loader, output_filename: str = "processed_solution.json", solution_file_name: str | None = None
):
    employees = loader.get_employees()
    shifts = loader.get_shifts()

    solution_files = loader.load_solution_file_names()

    if not solution_file_name:
        solution_file_name = solution_files[-1]

    solution = loader.get_solution(solution_file_name)

    stats = analyze_solution(solution.variables, employees, shifts)

    day_info = collect_day_information(solution, employees, shifts, loader)

    data = {
        "solution_file_names": solution_files,
        "selected_solution_file_name": solution_file_name,
        "variables": solution.variables,
        "employees": [employee_to_dict(e) for e in employees],
        "days": day_info["days"],
        "shifts": [shift_to_dict(s) for s in shifts],
        "stats": stats,
        "fulfilled_shift_wish_cells": day_info["fulfilled_shift_wish_cells"],
        "fulfilled_day_off_cells": day_info["fulfilled_day_off_cells"],
        "all_shift_wish_colors": day_info["all_shift_wish_colors"],
        "all_day_off_wish_cells": day_info["all_day_off_wish_cells"],
    }

    if not os.path.exists("processed_solutions"):
        os.makedirs("processed_solutions")

    with open("processed_solutions/" + output_filename, "w") as f:
        json.dump(data, f, indent=4, default=str)

    print(f"Exported solution data to {output_filename}")
