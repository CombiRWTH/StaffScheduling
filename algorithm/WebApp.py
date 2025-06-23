# algorithm/WebApp.py
# Simple Flask app to display staff scheduling results and file browsing

import json
import os
import ast
from datetime import datetime, timedelta
from flask import Flask, render_template, abort, request

# Base directory of the project
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Folders relative to BASE_DIR
SOLUTIONS_DIR = os.path.join(BASE_DIR, "found_solutions")
CASES_DIR = os.path.join(BASE_DIR, "cases")
CASE_ID = 1


# List available JSON files sorted by modification time (newest first)
def list_solution_files():
    if not os.path.isdir(SOLUTIONS_DIR):
        return []
    files = []
    for fname in os.listdir(SOLUTIONS_DIR):
        if not fname.lower().endswith(".json"):
            continue
        path = os.path.join(SOLUTIONS_DIR, fname)
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        files.append((mtime, fname))
    files.sort(key=lambda x: x[0], reverse=True)
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


app = Flask(__name__)


@app.route("/")
def index():
    files = list_solution_files()
    if not files:
        abort(404, description="Keine Lösungsdateien gefunden")

    current_file = request.args.get("file", files[0])
    try:
        data = load_solution_file(current_file)
    except FileNotFoundError:
        data = load_solution_file(files[0])
        current_file = files[0]

    solution_index = int(request.args.get("solution_index", 0))

    emp_map = data.get("employees", {}).get("name_to_index", {})
    if emp_map:
        employees = [None] * len(emp_map)
        for name, idx in emp_map.items():
            employees[idx] = {
                "name": name,
                "target": data["employees"].get("name_to_target", {}).get(name, 0) / 60,
            }
    else:
        employees = load_employees()

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
    # Initialize stats
    min_counts = {}
    max_counts = {}
    emp_work_hours = {}
    longest_streak = {}
    longest_night_streak = {}

    if total_solutions == 0:
        dates = []
        dates_info = []
        schedule_map = {}
        date_counts = {}
        shift_counts = {}
        shift_symbols = {0: "F", 1: "S", 2: "N", 3: "Z"}
        shift_labels = {
            0: "Frühschicht",
            1: "Spätschicht",
            2: "Nachtschicht",
            3: "Zwischenschicht",
        }
    else:
        if solution_index < 0 or solution_index >= total_solutions:
            solution_index = total_solutions - 1

        sample = sols[0]
        dates = sorted({d for (_, d, _) in sample.keys()})
        dates_info = []
        for date_str in dates:
            dt = datetime.strptime(date_str, "%Y-%m-%d").date()
            dates_info.append(
                {
                    "date": date_str,
                    "weekday": dt.strftime("%A"),
                    "is_weekend": dt.weekday() >= 5,
                }
            )

        num_employees = len(emp_map) if emp_map else len(employees)
        num_shifts = max((s for (_, _, s) in sample.keys()), default=-1) + 1
        shift_symbols = {0: "F", 1: "S", 2: "N", 3: "Z"}
        shift_labels = {
            0: "Frühschicht",
            1: "Spätschicht",
            2: "Nachtschicht",
            3: "Zwischenschicht",
        }

        sched = sols[solution_index]
        schedule_map = {i: {} for i in range(num_employees)}
        for (i, d, s), val in sched.items():
            if val:
                schedule_map[i][d] = s

        shift_counts = {i: len(schedule_map[i]) for i in schedule_map}

        # Load and compute work hours if available
        shift_durations = data.get("shiftDurations") or data.get("shift_durations")
        if shift_durations is None:
            shift_durations = {
                "F": 460,  # Frühschicht
                "S": 460,  # Spätschicht
                "N": 565,  # Nachtschicht
                "Z": 460,  # Zwischenschicht
            }
        if data.get("shiftDurations") or data.get("shift_durations"):
            shift_durations = data.get("shiftDurations") or data.get("shift_durations")
        emp_minutes = {i: 0 for i in range(num_employees)}
        for (i, d, s), val in sched.items():
            if val:
                symbol = shift_symbols.get(s)
                mins = shift_durations.get(symbol, 0)
                emp_minutes[i] += mins
        emp_work_hours = {i: round(m / 60, 1) for i, m in emp_minutes.items()}

        # Prepare date_counts
        date_counts = {d: {s: 0 for s in range(num_shifts)} for d in dates}
        for emp_idx, shifts in schedule_map.items():
            for d, s in shifts.items():
                date_counts[d][s] = date_counts[d].get(s, 0) + 1

        # Compute min/max per shift across dates
        for s in range(num_shifts):
            vals = [date_counts[d].get(s, 0) for d in dates]
            min_counts[s] = min(vals) if vals else 0
            max_counts[s] = max(vals) if vals else 0

        # Compute longest consecutive working days
        for i in range(num_employees):
            # sort employee's working dates
            worked_dates = sorted(
                datetime.strptime(d, "%Y-%m-%d").date() for d in schedule_map[i].keys()
            )
            max_run = 0
            current_run = 0
            prev_date = None
            for dt in worked_dates:
                if prev_date and dt == prev_date + timedelta(days=1):
                    current_run += 1
                else:
                    current_run = 1
                max_run = max(max_run, current_run)
                prev_date = dt
            longest_streak[i] = max_run

        # Compute longest consecutive night shifts
        night_symbol = None
        # find symbol index for 'N'
        for idx, sym in shift_symbols.items():
            if sym == "N":
                night_symbol = idx
        if night_symbol is not None:
            for i in range(num_employees):
                # dates with night shift
                night_dates = sorted(
                    datetime.strptime(d, "%Y-%m-%d").date()
                    for d, s in schedule_map[i].items()
                    if s == night_symbol
                )
                max_run = 0
                current_run = 0
                prev_date = None
                for dt in night_dates:
                    if prev_date and dt == prev_date + timedelta(days=1):
                        current_run += 1
                    else:
                        current_run = 1
                    max_run = max(max_run, current_run)
                    prev_date = dt
                longest_night_streak[i] = max_run

        # Tooltips for dates
        date_tooltips = {}
        for date, counts in date_counts.items():
            lines = []
            for s, cnt in counts.items():
                if cnt:
                    label = shift_labels.get(s, f"Schicht {s}")
                    lines.append(f"{label}: {cnt}")
            date_tooltips[date] = "\n".join(lines)

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
        num_days=len(dates),
        num_shifts=num_shifts,
        num_employees=len(employees),
        loaded_time=loaded_time,
        shift_symbols=shift_symbols,
        constraints=data.get("constraints", []),
        shift_counts=shift_counts,
        emp_work_hours=emp_work_hours,
        min_counts=min_counts,
        max_counts=max_counts,
        shift_labels=shift_labels,
        longest_streak=longest_streak,
        longest_night_streak=longest_night_streak,
    )


if __name__ == "__main__":
    app.jinja_env.add_extension("jinja2.ext.loopcontrols")
    app.run(debug=True, port=5010)
