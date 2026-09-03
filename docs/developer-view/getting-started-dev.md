# Getting Started (Developer View)

This guide walks you through setting up the local development environment for the **Staff Scheduling** project, configuring the TimeOffice database connection, running tests, and executing the solver and backend API.

---

## Prerequisites

--8<--
user-view/getting-started-light-version.md:Prerequisites
--8<--

### 3. Microsoft ODBC Driver 18 for SQL Server

The backend connects to the hospital's Microsoft SQL Server database via `pyodbc` and `SQLAlchemy`. You will need the **ODBC Driver 18 for SQL Server** installed on your machine:

* **Windows:** Download and install from [Microsoft Docs: ODBC Driver for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/windows/system-requirements-installation-and-driver-files).
* **Linux:** Follow the instructions for your distribution on [Microsoft Docs: Linux Installation](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server).
* **macOS:** Install via Homebrew: `brew install msodbcsql18` (see [Microsoft Docs: macOS Installation](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos)).

!!! tip "Alternative: Docker Development Container"
    If you do not wish to install the ODBC driver natively, the project provides a [`Dockerfile`](file:///c:/Users/jonas/Dev/StaffScheduling/Dockerfile) and [`Justfile`](file:///c:/Users/jonas/Dev/StaffScheduling/Justfile) that bundle Python 3.12, the ODBC Driver, and all dependencies in a Linux container. See [Running via Docker](#3-running-via-docker) below.

---

## Installation & Setup

--8<--
user-view/getting-started-light-version.md:Installation
--8<--

To install all optional dependencies (e.g. for building documentation):

```bash
uv sync --all-extras
```

### Configure Environment Variables (`.env`)

Create a `.env` file in the project root by copying the template:

```bash
cp .env.template .env
```

Edit `.env` to supply the TimeOffice database credentials:

```env
# TimeOffice Database
DB_DRIVER="ODBC Driver 18 for SQL Server"
DB_SERVER=your.database.server
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password

# Solver Configuration (Optional)
LOG_LEVEL=INFO
SOLVER_MAX_TIME_SECONDS=30
SOLVER_NUM_SEARCH_WORKERS=
SOLVER_LOG_SEARCH_PROGRESS=false
```

*(If you need database credentials, contact the team or Pradtke GmbH. For offline development, anonymized station datasets are available under `cases/`.)*

### Set Up Git Pre-Commit Hooks

We use `pre-commit` to automatically format code, trim whitespace, and enforce style rules before every commit:

```bash
uv run pre-commit install
```

To run all hooks manually across the entire codebase:

```bash
uv run pre-commit run --all-files
```

---

## Code Quality & Testing

The repository uses [`just`](https://github.com/casey/just) as a command runner for common development tasks.

```bash
# Run all quality checks (lint, typecheck, tests)
just check

# Run individual checks
just lint        # Ruff linting
just format      # Ruff formatting
just typecheck   # Pyright strict type checking
just test        # Pytest unit test suite
```

Alternatively, you can run tools directly with `uv`:

```bash
uv run ruff check .
uv run pyright .
uv run pytest tests
```

---

## Running the Application

### 1. Running the Solver via CLI

You can run the optimization solver directly from your terminal using the CLI entrypoint:

```bash
uv run --env-file .env staff-scheduling solve <planning_unit_id> <start_date> <end_date>
```

For example, to solve Station 77 for the entire month of November 2024:

```bash
uv run --env-file .env staff-scheduling solve 77 2024-11-01 2024-11-30
```

* Dates can be supplied as `YYYY-MM-DD` or `DD.MM.YYYY`.
* The solver operates on full calendar months (from the 1st to the last day of the month).
* The command connects to TimeOffice, fetches station personnel, demands, and preferences, runs CP-SAT, and exports the resulting schedule to `found_solutions/` and `processed_solutions/`.

### 2. Running the FastAPI Backend

To start the HTTP API server:

```bash
uv run fastapi dev src/scheduling/api/app.py --host 0.0.0.0 --port 8000
```

Once running, interactive API documentation is available at:

* **Swagger UI:** `http://127.0.0.1:8000/docs`
* **ReDoc:** `http://127.0.0.1:8000/redoc`

### 3. Running via Docker

If you prefer running inside a container:

```bash
# Build the Docker image
just build

# Start the FastAPI server with live source reload
just run

# Start with debugpy on port 5678
just debug
```

### 4. Running the Web Interface (StaffSchedulingWeb)

The graphical user interface is developed in a companion repository: **[StaffSchedulingWeb](https://github.com/julian466/StaffSchedulingWeb)**.

1. Start the backend API on port `8000` (`just run` or `uv run fastapi dev ...`).
2. Clone and start the Next.js frontend:
   ```bash
   git clone https://github.com/julian466/StaffSchedulingWeb.git
   cd StaffSchedulingWeb
   npm install
   npm run dev
   ```
3. Open `http://localhost:3000` in your browser.

For complete details on the frontend architecture and features, see the [Web Interface documentation](./web-interface.md).
