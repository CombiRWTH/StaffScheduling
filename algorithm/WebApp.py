# algorithm/WebApp.py
# Simple Flask app to display staff scheduling results and file browsing

import json
import os
import re
import ast
from datetime import datetime
from flask import Flask, render_template_string, abort, request

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
TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Staff Schedule - Case {{ case_id }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body { padding: 20px; }
    h1, h2 { margin-top: 20px; }
    th, td { text-align: center; vertical-align: middle; white-space: nowrap; }
    .shift-0 { background: #FFCCCC; }
    .shift-1 { background: #CCCCFF; }
    .shift-2 { background: #CCFFCC; }
  </style>
  <script>
    function changeFile(sel) {
      const file = encodeURIComponent(sel.value);
      const idx = document.getElementById('solSelect').value - 1;
      window.location.href = `/?file=${file}&solution_index=${idx}`;
    }
    function changeSolution(sel) {
      const sol = sel.value - 1;
      const file = encodeURIComponent(document.getElementById('fileSelect').value);
      window.location.href = `/?file=${file}&solution_index=${sol}`;
    }
  </script>
</head>
<body class="bg-light">
  <div class="container bg-white p-4 rounded shadow-sm" style="overflow-x:auto;">
    <h1 class="text-primary">Staff Schedule (Case {{ case_id }})</h1>

    <div class="row mb-3">
      <div class="col-md-6">
        <label for="fileSelect" class="form-label">Lösung Datei</label>
        <select id="fileSelect" class="form-select" onchange="changeFile(this)">
          {% for f in solution_files %}
            <option value="{{ f }}" {% if f == current_file %}selected{% endif %}>{{ f }}</option>
          {% endfor %}
        </select>
      </div>
      <div class="col-md-6">
        <label for="solSelect" class="form-label">Lösung Nummer</label>
        <select id="solSelect" class="form-select" onchange="changeSolution(this)">
          {% for i in range(1, total_solutions + 1) %}
            <option value="{{ i }}" {% if i-1 == solution_index %}selected{% endif %}>{{ i }}</option>
          {% endfor %}
        </select>
      </div>
    </div>

    <h2>Ansicht {{ solution_index + 1 }} von {{ total_solutions }}</h2>

    <div class="table-responsive">
      <table class="table table-striped table-hover table-bordered">
        <thead class="table-light">
          <tr>
            <th scope="col">Mitarbeiter</th>
            {% for date in dates %}<th scope="col">{{ date }}</th>{% endfor %}
          </tr>
        </thead>
        <tbody>
          {% for emp in employees %}
            {% set idx = loop.index0 %}
            <tr>
              <td title="{{ shift_counts[idx] }} Schichten">{{ emp['name'] }}</td>
              {% for date in dates %}
                {% set shift = schedule_map[idx].get(date) %}
                <td class="shift-{{ shift if shift is not none else '' }}">
                  {{ shift_symbols[shift] if shift is not none else '' }}
                </td>
              {% endfor %}
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <h2>Debug & Parameter</h2>
    <ul>
      <li>Fall ID: {{ case_id }}</li>
      <li>Geplante Tage: {{ num_days }}</li>
      <li>Mitarbeiter: {{ num_employees }}</li>
      <li>Schichten pro Tag: {{ num_shifts }}</li>
      <li>Geladen um: {{ loaded_time }}</li>
      <li>Constraints: {{ constraints | join(', ') }}</li>
      <li>Anzahl Lösungen: {{ total_solutions }}</li>
    </ul>
  </div>
</body>
</html>
"""

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

    return render_template_string(
        TEMPLATE,
        case_id=CASE_ID,
        solution_files=files,
        current_file=current_file,
        solution_index=solution_index,
        total_solutions=total_solutions,
        employees=employees,
        schedule_map=schedule_map,
        dates=dates,
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
