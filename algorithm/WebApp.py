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
    if solution_index < 0 or solution_index >= total_solutions:
        abort(404)

    sample = sols[0]
    dates = sorted({d for (_, d, _) in sample.keys()})
    num_days = len(dates)
    num_employees = len(employees)
    num_shifts = max(s for (_, _, s) in sample.keys()) + 1
    loaded_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    shift_symbols = {0: "F", 1: "S", 2: "N"}

    sched = sols[solution_index]
    schedule_map = {i: {} for i in range(num_employees)}
    for (i, d, s), val in sched.items():
        if val:
            schedule_map[i][d] = s

    shift_counts = {i: len(schedule_map[i]) for i in schedule_map}

    # shift_labels für die Beschriftung
    shift_labels = {0: "Frühschichten", 1: "Spätschichten", 2: "Nachtschichten"}

    # 1) Zähle die Schichten pro Tag
    date_counts = {d: {s: 0 for s in range(num_shifts)} for d in dates}
    for emp_idx, shifts in schedule_map.items():
        for d, s in shifts.items():
            date_counts[d][s] += 1

    # 2) Tooltip-Texte pro Datum zusammenbauen
    date_tooltips = {}
    for date, counts in date_counts.items():
        lines = []
        for s, cnt in counts.items():
            if cnt:
                label = shift_labels.get(s, f"Schicht {s}")
                lines.append(f"{label}: {cnt}")
        # mehreren Zeilen durch newline trennen
        date_tooltips[date] = "\n".join(lines)

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
