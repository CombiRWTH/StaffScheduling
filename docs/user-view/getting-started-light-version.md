# Getting Started (Light Version)

This guide walks you through running the **Staff Scheduling** solver locally **without a database connection**, using pre-exported JSON case files. This is ideal for experimenting with the solver, testing new constraints, or understanding the scheduling output without access to the hospital's TimeOffice system.

---

# --8<-- [start:Prerequisites]
## Prerequisites

Before setting up the project, make sure the following tools are installed on your system:

### 1. Install [Python 3.12+](https://www.python.org/downloads/)

This project requires **Python 3.12 or higher**.

Open your terminal (Mac) or Command Prompt (Windows). Check whether and which version of python you have installed by running:

```bash
python3 --version
```

If not installed, download it from the official website: [https://www.python.org/downloads/](https://www.python.org/downloads/) and install it.

### 2. Install `uv`

uv is a fast Python package manager used to create and manage isolated environments. You can install it following the instructions in the official documentation:

[https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)
# --8<-- [end:Prerequisites]

---
# --8<-- [start:Installation]
## Installation

Follow these steps to set up the development environment.

### 1. Download our Project

In order to use our application you need to download the code from [Github](https://github.com/CombiRWTH/StaffScheduling). If you are familiar with Github, you can simply clone the project, if not, you can click on the green "Code" button and choose to download as zip file, which you need to unpack. Then open a command line tool (terminal or command prompt) to navigate to the project folder.

### 2. Install dependencies

Make sure [`uv`](https://github.com/astral-sh/uv) is installed.

```bash
uv sync
```

This will install all required dependencies.
# --8<-- [end:Installation]

---

## Understanding Cases

The `cases/` directory contains anonymized snapshots of real ward data exported from TimeOffice. Each case represents one **planning unit** (a hospital ward or station) and is organized by unit ID:

```
cases/
├── 77/                    # Planning unit 77
│   └── 11_2024/           # November 2024
│       ├── employees.json
│       ├── employee_types.json
│       ├── free_shifts_and_vacation_days.json
│       ├── general_settings.json
│       ├── minimal_number_of_staff.json
│       ├── shift_information.json
│       ├── target_working_minutes.json
│       ├── wishes_and_blocked.json
│       └── worked_sundays.json
├── 78/
│   └── ...
```

The month folder is named `{MM}_{YYYY}` (e.g. `11_2024` for November 2024). The loader checks this folder first; a fallback `cases/{case_id}/` folder can hold shared configuration used across months.

For a full description of each JSON file's format, see the [JSON Data Formats](../developer-view/json-dataformat.md) reference.

---

## Usage

### Solve via the Web Interface

Use **StaffSchedulingWeb** to configure, start, and inspect solves in a browser — no command line required:

1. Start the backend API:
   ```bash
   uv run fastapi dev src/scheduling/api/app.py --host 0.0.0.0 --port 8000
   ```
2. Open the [StaffSchedulingWeb documentation](https://julian466.github.io/StaffSchedulingWeb/) and follow the setup steps there.
3. Use the UI to select your case and planning period, start the solver, and inspect results.

### Solve via Command Line

You can also run the solver directly from the terminal without a database — but note the CLI currently requires a database connection. For offline JSON-based runs, use the FastAPI + StaffSchedulingWeb approach above with the JSON loader.

!!! tip "Working Offline"
    The available anonymized case files (e.g. `cases/77/11_2024/`) can be loaded through the web interface using the **Import JSON** feature in StaffSchedulingWeb. This lets you run the full solver without any database credentials.

---

## Interpreting the Output

After a successful solve, the results appear in two directories:

### `found_solutions/`

Contains the raw solver output in JSON format:
```
found_solutions/
└── solution_77_2024-11-01-2024-11-30_wdefault.json
```

The file contains the full list of generated shift assignments:
```json
{
  "status": "optimal",
  "assignments": [
    {
      "employee_id": 101,
      "date": "2024-11-01",
      "shift_id": 1113,
      "planning_unit_id": 77,
      "type": "generated"
    }
  ],
  "diagnostics": [],
  "audit": { "findings": [] }
}
```

- `status`: `"optimal"` means the solver found the best possible schedule within the time limit; `"feasible"` means a valid schedule was found but further improvement may be possible.
- `assignments`: The complete list of shift assignments produced by the solver.
- `audit.findings`: Any constraint violations detected by the post-solve audit engine.

### `processed_solutions/`

Contains the solution converted into the legacy TimeOffice import format (for write-back into the system). These files are used internally by the TimeOffice integration layer.

---

## Tuning the Solver

You can influence solve quality by adjusting the `.env` file:

| Setting | Default | Effect |
|---|---|---|
| `SOLVER_MAX_TIME_SECONDS` | `30` | Increase for better solution quality on complex cases |
| `SOLVER_NUM_SEARCH_WORKERS` | `auto` | Set to the number of CPU cores for faster search |
| `SOLVER_LOG_SEARCH_PROGRESS` | `false` | Set to `true` to see live solver output |

For objective weights (how much to prioritize wishes vs. overtime vs. fairness), see [Adapting Weights](./configuration/weights.md).
