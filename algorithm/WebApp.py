# algorithm/WebApp.py
# Simple Flask app to display staff scheduling results and file browsing

import json
import os
import re
import ast
from datetime import datetime
from flask import Flask, render_template, abort, request

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Folders relative to BASE_DIR
SOLUTIONS_DIR = os.path.join(BASE_DIR, "found_solutions")
CASES_DIR = os.path.join(BASE_DIR, "cases")
CASE_ID = 1

# Pattern for solution files
PATTERN = re.compile(r"solutions_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})\.json$")


# List available solution files sorted by timestamp
def list_solution_files():
    if not os.path.isdir(SOLUTIONS_DIR):
        return []
    files = []
    for fname in os.listdir(SOLUTIONS_DIR):
        match = PATTERN.match(fname)
        if not match:
            continue
        date_part, time_part = match.groups()
        ts_str = f"{date_part} {time_part.replace('-', ':')}"
        try:
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        files.append((ts, fname))
    files.sort(key=lambda x: x[0])
    return [fname for _, fname in files]


# Load a specific solution file by filename
def load_solution_file(filename):
    path = os.path.join(SOLUTIONS_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Solution file not found: {filename}")
    with open(path, "r") as f:
        return json.load(f)


# Optional fallback: load employees from cases folder
def load_employees(case_id=CASE_ID):
    path = os.path.join(CASES_DIR, str(case_id), "employees.json")
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)


# HTML template using Jinja2 and Bootstrap for styling
app = Flask(__name__)


@app.route("/")
def index():
    # Available files
    files = list_solution_files()
    if not files:
        abort(404, description="Keine Lösungsdateien gefunden")

    # Get query params
    current_file = request.args.get("file", files[-1])
    try:
        data = load_solution_file(current_file)
    except FileNotFoundError:
        data = load_solution_file(files[-1])
        current_file = files[-1]

    solution_index = int(request.args.get("solution_index", 0))

    # Build employees
    emp_map = data.get("employees", {}).get("name_to_index", {})
    if emp_map:
        employees = [None] * len(emp_map)
        for name, idx in emp_map.items():
            employees[idx] = {"name": name}
    else:
        employees = load_employees()

    # Parse solutions
    raw = data.get("solutions", [])
    sols = []
    for sol in raw:
        conv = {}
        for k, v in sol.items():
            try:
                tup = ast.literal_eval(k)
                conv[tup] = v
            except Exception:
                continue
        sols.append(conv)

    total_solutions = len(sols)
    # Special Case: no solution → render empty schedule
    if total_solutions == 0:
        dates = []
        dates_info = []
        date_counts = {}
        num_days = 0
        num_shifts = 0
        num_employees = len(employees)
        shift_symbols = {0: "F", 1: "S", 2: "N", 3: "Z"}
        schedule_map = {i: {} for i in range(num_employees)}
        shift_counts = {i: 0 for i in range(num_employees)}
        date_tooltips = {}
    else:
        if solution_index < 0 or solution_index >= total_solutions:
            abort(404)

        # first solution
        sample = sols[0]
        # dates
        dates = sorted({d for (_, d, _) in sample.keys()})
        dates_info = []
        for date_str in dates:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
            dates_info.append(
                {
                    "date": date_str,
                    "weekday": dt.strftime("%A"),  # z.B. "Montag"
                    "is_weekend": dt.weekday() >= 5,  # Samstag=5, Sonntag=6
                }
            )
        num_days = len(dates)
        num_employees = len(employees)
        num_shifts = max(s for (_, _, s) in sample.keys()) + 1
        shift_symbols = {0: "F", 1: "S", 2: "N", 3: "Z"}

        # select solution
        sched = sols[solution_index]
        schedule_map = {i: {} for i in range(num_employees)}
        for (i, d, s), val in sched.items():
            if val:
                schedule_map[i][d] = s

        # Stats for hovering Employee names
        shift_counts = {i: len(schedule_map[i]) for i in schedule_map}

        # shift_labels for hovering dates
        shift_labels = {
            0: "Frühschicht",
            1: "Spätschicht",
            2: "Nachtschicht",
            3: "Zwischenschicht",
        }

        # 1) count daily shifts
        date_counts = {d: {s: 0 for s in range(num_shifts)} for d in dates}
        for emp_idx, shifts in schedule_map.items():
            for d, s in shifts.items():
                date_counts[d][s] += 1

        # 2) create tooltip texts
        date_tooltips = {}
        for date, counts in date_counts.items():
            lines = []
            for s, cnt in counts.items():
                if cnt:
                    label = shift_labels.get(s, f"Schicht {s}")
                    lines.append(f"{label}: {cnt}")
            date_tooltips[date] = "\n".join(lines)

    # debug create time
    loaded_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return render_template(
        "index.html",
        case_id=CASE_ID,
        solution_files=files,
        current_file=current_file,
        solution_index=solution_index,
        total_solutions=total_solutions,
        employees=employees,
        schedule_map=schedule_map,
        dates=dates,
        dates_info=dates_info,
        date_counts=date_counts,
        date_tooltips=date_tooltips,
        num_days=num_days,
        num_shifts=num_shifts,
        num_employees=num_employees,
        loaded_time=loaded_time,
        shift_symbols=shift_symbols,
        constraints=data.get("constraints", []),
        shift_counts=shift_counts,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
