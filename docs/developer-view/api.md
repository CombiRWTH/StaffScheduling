# API

This project provides a FastAPI-based HTTP interface so the solver can be used without the CLI.

## Start the API

```bash
uv run staff-scheduling-api
```

By default the API runs on:

- `http://127.0.0.1:8000`

Interactive API docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### `GET /status`

Returns the current solver state. This endpoint is useful for
monitoring progress from a frontend or another automation script
without blocking on the solver request.

The `phase` field reflects the internal solver step which helps
present a progress bar. The strings are emitted directly from the
solver and should be interpreted as follows:

- `idle` – no solver is running
- `phase_1_upper_bound` – first pass to compute an upper bound on hidden
  employees (fast, relaxes staffing constraints)
- `phase_2_tight_bound` – second pass tuning hidden‑employee counts to a
  tight bound
- `phase_3_optimizing` – main optimization/search phase (respects the
  `timeout` parameter)

Example response:

```json
{
  "is_solving": false,
  "phase": "idle",
  "timeout_set_for_phase_3": 0
}
```

Additional properties during a multi‑solve run:

- `weight_id` – index of the current weight configuration
- `total_weights` – number of iterations planned

### `POST /fetch`

Exports planning data from TimeOffice to local case JSON files.

**Request body:**

```json
{
  "planning_unit": 77,
  "from_date": "2024-11-01",
  "till_date": "2024-11-30"
}
```

**Response:**

```json
{
  "success": true,
  "log": "...captured log output...",
  "stdout": "...captured console output..."
}
```

`success` is always `true` when the request completes without errors; any
failure will raise an HTTP 500 error with a message.

### `POST /solve`

Runs one solver execution for the given planning period.

**Request body:**

```json
{
  "unit": 77,
  "start_date": "2024-11-01",
  "end_date": "2024-11-30",
  "timeout": 300
}
```

**Response:**

```json
{
  "success": true,
  "status": "OPTIMAL",
  "log": "...captured log output...",
  "stdout": "...captured console output..."
}
```

`success` is `true` when the solver returns `FEASIBLE` or `OPTIMAL`;
otherwise it is `false` and `status` holds the actual OR-Tools return code
(e.g. `INFEASIBLE`, `UNKNOWN`).

### `POST /solve-multiple`

Runs three solver executions with different weight presets.

**Request body:**

```json
{
  "unit": 77,
  "start_date": "2024-11-01",
  "end_date": "2024-11-30",
  "timeout": 300
}
```

**Response:**

```json
{
  "success": true,
  "statuses": ["OPTIMAL", "FEASIBLE", "INFEASIBLE"],
  "log": "...captured log output...",
  "stdout": "...captured console output..."
}
```

`statuses` contains the OR-Tools statuses for each iteration; `success`
becomes `true` if any of them is `FEASIBLE` or `OPTIMAL`.

### `POST /insert`

Inserts a previously generated solution into the TimeOffice database.

**Request body:**

```json
{
  "planning_unit": 77,
  "from_date": "2024-11-01",
  "till_date": "2024-11-30"
}
```

**Response:**

```json
{
  "success": true,
  "log": "...captured log output...",
  "stdout": "...captured console output..."
}
```

As with `/fetch`, `success` is `true` on normal completion; errors return
HTTP 500.

### `POST /delete`

Deletes a previously inserted solution from the TimeOffice database.

**Request body:**

```json
{
  "planning_unit": 77,
  "from_date": "2024-11-01",
  "till_date": "2024-11-30"
}
```

**Response:**

```json
{
  "success": true,
  "log": "...captured log output...",
  "stdout": "...captured console output..."
}
```

## Typical API Workflow

1. `POST /fetch`
2. `POST /solve` or `POST /solve-multiple`
3. Poll `GET /status` while solving
4. `POST /insert` to write the selected solution to TimeOffice
5. Optional: `POST /delete` to revert inserted solution data
