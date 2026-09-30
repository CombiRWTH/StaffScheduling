# Staff Scheduling Optimization in Hospitals

Welcome to the Staff Scheduling Optimization project repository! This project was developed by students from the Chair of Combinatorial Optimization at RWTH Aachen University in collaboration with St. Marien-Hospital Düren and Pradtke GmbH.

The primary aim of this project is to automate the existing scheduling process within hospitals using TimeOffice software. The system extracts planning data from TimeOffice, solves a constrained combinatorial optimization problem via Google OR-Tools CP-SAT, and persists the generated schedule back into TimeOffice.

---

## Quickstart

### Prerequisites

* **Python 3.12+**
* [**`uv`**](https://docs.astral-sh/uv/) package manager
* *(Optional)* Microsoft ODBC Driver 18 for SQL Server (for live database connectivity)

### Installation

```shell
git clone https://github.com/CombiRWTH/StaffScheduling.git
cd StaffScheduling
uv sync
```

### Running the Application

* **Start the FastAPI Backend:**
  ```shell
  uv run fastapi dev src/scheduling/api/app.py --host 0.0.0.0 --port 8000
  ```

* **Run via CLI:**
  ```shell
  uv run staff-scheduling solve <planning_unit_id> <start_date> <end_date>
  # Example: uv run staff-scheduling solve 77 2024-11-01 2024-11-30
  ```

* **Web Interface:**
  The frontend is available in the companion repository [**StaffSchedulingWeb**](https://github.com/julian466/StaffSchedulingWeb).

---

## Documentation

* **Online Documentation 🌐:** [https://combirwth.github.io/StaffScheduling/](https://combirwth.github.io/StaffScheduling/)
* **Run Documentation Locally 📚:**
  ```shell
  uv sync --extra docs
  uv run mkdocs serve
  ```
