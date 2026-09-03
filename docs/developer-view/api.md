# API Reference

The Staff Scheduling system provides a RESTful HTTP interface built with **FastAPI**. It powers the **[StaffSchedulingWeb](https://julian466.github.io/StaffSchedulingWeb/)** frontend and allows programmatic execution of the solver, data synchronization with the TimeOffice database, and configuration of planning parameters.

---

## Endpoint Overview

| Endpoint | Methods | Description |
|---|---|---|
| **Health Check** | | |
| [`/status`](#get-status) | `GET` | Healthcheck verifying API server availability. |
| **Optimization (`/solve`)** | | |
| [`/solve/options`](#get-solveoptions) | `GET` | Fetch selectable planning units (wards/stations) from TimeOffice. |
| [`/solve/`](#post-solve) | `POST` | Asynchronously trigger a schedule optimization job (`202 Accepted`). |
| [`/solve/jobs/{job_id}`](#get-solvejobsjob_id) | `GET` | Poll job lifecycle state (`running`, `succeeded`, `failed`) and get results. |
| **Ward & Staff Configuration** | | |
| [`/employees`](#get-employees) | `GET` | Retrieve employees and qualification levels for a planning unit and month. |
| [`/minimal-staff`](#minimal-staffing-demand-minimal-staff) | `GET`, `PUT` | View or update minimum staffing demand requirements in TimeOffice. |
| [`/weights`](#objective-function-weights-weights) | `GET`, `PUT` | View or update penalty weights for CP-SAT soft objectives. |
| [`/wishes-and-blocked`](#employee-wishes--availabilities-wishes-and-blocked) | `GET` | Retrieve employee shift wishes, preferred days, and absences/leaves. |
| [`/wishes-and-blocked/{employee_id}`](#put-wishes-and-blockedemployee_id) | `PUT`, `DELETE` | Replace or delete an employee's shift wishes and non-vacation blocked days. |
| **Schedule Solutions (`/schedules`)** | | |
| [`/schedules/metadata`](#metadata--discovery) | `GET`, `PUT` | List or update available generated schedules, timestamps, and active selection. |
| [`/schedules/{schedule_id}`](#solution-content) | `GET`, `PUT`, `DELETE` | Fetch, save, or delete a specific schedule solution. |
| [`/schedules/last-inserted`](#timeoffice-active-marker-scheduleslast-inserted) | `GET`, `PUT`, `DELETE` | Get, set, or clear the marker for the schedule currently active in TimeOffice. |

---

## Getting Started

### Start the API Server

You can run the API locally using `uv`:

```bash
uv run fastapi dev src/scheduling/api/app.py --host 0.0.0.0 --port 8000
```

Alternatively, if using the project's [`Justfile`](file:///c:/Users/jonas/Dev/StaffScheduling/Justfile) with Docker:

```bash
# Run in development container
just run

# Run with debugpy enabled on port 5678
just debug
```

By default, the server listens on:

* **Base URL:** `http://127.0.0.1:8000`
* **Interactive OpenAPI (Swagger UI):** `http://127.0.0.1:8000/docs`
* **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

---

## General Endpoints

### `GET /status`

Simple healthcheck endpoint to verify that the API server is up and responsive.

**Response:**

```json
{
  "status": "healthy"
}
```

---

## Solver Endpoints (`/solve`)

The solver runs **asynchronously in the background** to prevent long-running optimization tasks from blocking HTTP requests. Only one solve job can run at a time; a concurrency lock returns an HTTP `423 Locked` status if another job is already in progress.

### `GET /solve/options`

Retrieves the available planning units (wards/stations) from the TimeOffice database that can be targeted for roster generation.

**Response:**

```json
{
  "planning_units": [
    {
      "planning_unit_id": 77,
      "code": "ST77",
      "display_name": "Station 77 (Innere Medizin)",
      "type": "standard"
    },
    {
      "planning_unit_id": 78,
      "code": "ST78",
      "display_name": "Station 78 (Chirurgie)",
      "type": "standard"
    }
  ]
}
```

### `POST /solve/`

Submits a new schedule optimization task. The request returns immediately with an HTTP `202 Accepted` status and a unique `job_id` for tracking.

**Request Body:**

```json
{
  "planning_unit_ids": [77],
  "year": 2024,
  "month": 11
}
```

| Field | Type | Description |
|---|---|---|
| `planning_unit_ids` | `list[int]` | Non-empty list of planning unit IDs to optimize. |
| `year` | `int` | Planning year (between 2000 and 2100). |
| `month` | `int` | Planning month (1–12). |

**Response (`202 Accepted`):**

```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "accepted"
}
```

**Error Responses:**

* `422 Unprocessable Entity`: Invalid date or empty `planning_unit_ids`.
* `423 Locked`: The solver is currently busy solving another job. Try again later.

### `GET /solve/jobs/{job_id}`

Retrieves the status, execution metadata, and results of a submitted solve job.

**Path Parameters:**

* `job_id` (`UUID`): The job identifier returned by `POST /solve/`.

**Response (In Progress):**

```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "running",
  "command": {
    "planning_unit_ids": [77],
    "planning_month": {
      "year": 2024,
      "month": 11
    }
  },
  "created_at": "2024-11-01T10:00:00Z",
  "started_at": "2024-11-01T10:00:01Z",
  "finished_at": null,
  "result": null,
  "error": null
}
```

**Job Statuses:**

* `accepted`: Job is enqueued and waiting to acquire solver resources.
* `running`: Data has been fetched from TimeOffice and CP-SAT is optimizing.
* `succeeded`: The solver finished successfully. The `result` field contains the generated assignments, diagnostics, and audit report.
* `failed`: An error occurred during fetching or solving; details are stored in the `error` field.

**Response (Succeeded):**

When `status` is `succeeded`, `result` contains the solved schedule:

```json
{
  "job_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "succeeded",
  "command": {
    "planning_unit_ids": [77],
    "planning_month": { "year": 2024, "month": 11 }
  },
  "created_at": "2024-11-01T10:00:00Z",
  "started_at": "2024-11-01T10:00:01Z",
  "finished_at": "2024-11-01T10:00:18Z",
  "result": {
    "status": "optimal",
    "assignments": [
      {
        "employee_id": 101,
        "date": "2024-11-01",
        "shift_id": 1113,
        "planning_unit_id": 77,
        "type": "assigned"
      }
    ],
    "diagnostics": [],
    "audit": {
      "findings": []
    }
  },
  "error": null
}
```

---

## Pre-Planning & Configuration Endpoints

These endpoints read and write planning configuration parameters stored in TimeOffice and consumed by the web interface. All query parameters require `planning_unit` (`int`) and `from_date` (`YYYY-MM-DD`).

### Employees (`/employees`)

#### `GET /employees`

Returns all employees assigned to a planning unit for the given month, along with their qualification level.

**Query Parameters:**
* `planning_unit` (`int`): e.g. `77`
* `from_date` (`date`): e.g. `2024-11-01`

**Response:**

```json
{
  "employees": [
    {
      "key": 101,
      "name": "Mustermann",
      "firstname": "Erika",
      "type": "professional"
    },
    {
      "key": 102,
      "name": "Schmidt",
      "firstname": "Max",
      "type": "assistant"
    }
  ]
}
```

---

### Minimal Staffing Demand (`/minimal-staff`)

Manages the minimum required staff count per shift, qualification level, and weekday.

#### `GET /minimal-staff`

**Response:**

```json
{
  "Fachkraft": {
    "Mo": { "F": 3, "S": 2, "N": 1, "Z": 0 },
    "Di": { "F": 3, "S": 2, "N": 1, "Z": 0 },
    "Mi": { "F": 3, "S": 2, "N": 1, "Z": 0 },
    "Do": { "F": 3, "S": 2, "N": 1, "Z": 0 },
    "Fr": { "F": 3, "S": 2, "N": 1, "Z": 0 },
    "Sa": { "F": 2, "S": 2, "N": 1, "Z": 0 },
    "So": { "F": 2, "S": 2, "N": 1, "Z": 0 }
  },
  "Hilfskraft": { ... },
  "Azubi": { ... }
}
```

* Shift abbreviations: `F` (Early / *Frühdienst*), `S` (Late / *Spätdienst*), `N` (Night / *Nachtdienst*), `Z` (Intermediate / *Zwischendienst*).

#### `PUT /minimal-staff`

Persists updated staffing requirements into TimeOffice.

**Request Body:**

```json
{
  "data": {
    "Fachkraft": {
      "Mo": { "F": 3, "S": 2, "N": 1, "Z": 0 }
    }
  }
}
```

**Response:** `{"success": true}`

---

### Objective Function Weights (`/weights`)

Adjusts the penalty multipliers used by the CP-SAT solver when balancing trade-offs between competing soft objectives.

#### `GET /weights`

**Response:**

```json
{
  "after_night": 10,
  "consecutive_days": 15,
  "consecutive_nights": 20,
  "fairness": 5,
  "free_weekend": 25,
  "hidden": 50,
  "overtime": 30,
  "rotate": 10,
  "second_weekend": 20,
  "wishes": 40
}
```

#### `PUT /weights`

Updates the objective penalty weights for the planning unit.

**Request Body:**

```json
{
  "data": {
    "after_night": 10,
    "consecutive_days": 15,
    "consecutive_nights": 20,
    "fairness": 5,
    "free_weekend": 25,
    "hidden": 50,
    "overtime": 30,
    "rotate": 10,
    "second_weekend": 20,
    "wishes": 40
  }
}
```

**Response:** `{"success": true}`

---

### Employee Wishes & Availabilities (`/wishes-and-blocked`)

Manages employee preferences (desired free days or preferred shifts) and availability constraints (absences, vacations, blocked days).

#### `GET /wishes-and-blocked`

Returns employees who have registered wishes or blocked times for the target month.

**Response:**

```json
{
  "employees": [
    {
      "key": 101,
      "firstname": "Erika",
      "name": "Mustermann",
      "blocked_days": [14, 15],
      "blocked_shifts": [[10, "N"]],
      "wish_days": [22],
      "wish_shifts": [[5, "F"]],
      "work_days": [],
      "work_shifts": []
    }
  ]
}
```

#### `PUT /wishes-and-blocked/{employee_id}`

Replaces the wishes and blocked times for an individual employee.

**Request Body:**

```json
{
  "data": {
    "key": 101,
    "firstname": "Erika",
    "name": "Mustermann",
    "blocked_days": [14, 15],
    "blocked_shifts": [[10, "N"]],
    "wish_days": [22],
    "wish_shifts": [[5, "F"]],
    "work_days": [],
    "work_shifts": []
  }
}
```

**Response:** `{"success": true}`

#### `DELETE /wishes-and-blocked/{employee_id}`

Removes all wishes and non-vacation availability blocks for the employee in that planning month.

**Response:** `{"success": true}`

---

## Schedule & Solution Management (`/schedules`)

Endpoints for retrieving, saving, and inspecting generated rosters.

### Metadata & Discovery

#### `GET /schedules/metadata`

Discovers available solved schedules for a planning unit and returns metadata such as generation timestamps and summary stats.

**Response:**

```json
{
  "schedules": [
    {
      "scheduleId": "solution_77_2024-11-01-2024-11-30_wdefault",
      "description": "Solver-generiert: solution_77_2024-11-01-2024-11-30_wdefault",
      "generatedAt": "2024-11-01T10:15:30Z",
      "isSelected": true,
      "stats": {}
    }
  ],
  "selectedScheduleId": "solution_77_2024-11-01-2024-11-30_wdefault"
}
```

#### `PUT /schedules/metadata`

Updates metadata (such as which schedule is currently selected in the UI).

**Response:** `{"success": true}`

---

### Solution Content

#### `GET /schedules/{schedule_id}`

Fetches the complete schedule data for a specific solution identifier.

**Response:**

```json
{
  "solution": {
    "status": "optimal",
    "assignments": [ ... ],
    "stats": { ... }
  }
}
```

#### `PUT /schedules/{schedule_id}`

Saves modifications to a schedule solution.

#### `DELETE /schedules/{schedule_id}`

Deletes a saved schedule solution file.

---

### TimeOffice Active Marker (`/schedules/last-inserted`)

Tracks which schedule was last inserted into the hospital's live TimeOffice roster.

* `GET /schedules/last-inserted`: Returns the identifier and timestamp of the schedule currently marked as inserted.
* `PUT /schedules/last-inserted`: Sets the active inserted schedule marker.
* `DELETE /schedules/last-inserted`: Clears the active schedule marker.
