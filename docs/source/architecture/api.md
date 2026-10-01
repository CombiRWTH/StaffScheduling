# API

This reference describes inspected source definitions. Connected database behavior and complete user workflows require separate acceptance evidence; see [current limitations](../validation/index.md).

The FastAPI application is `api/app/main.py`. With Compose running, open <http://localhost:8000/docs> for interactive request/response schemas, or <http://localhost:8000/openapi.json> for OpenAPI. Schemas reflect the current checkout.

## Routes

Consult OpenAPI for exact bodies and responses.

| Route                  | Methods | Current behavior                                          |
| ---------------------- | ------- | --------------------------------------------------------- |
| `/status`              | GET     | Process liveness without a TimeOffice query               |
| `/planning/options`    | GET     | Named stations with unique full-month targets             |
| `/employees`           | GET     | Complete canonical combined month/station/pool inspection |
| `/solve/`              | POST    | Accept a full-month solve job                             |
| `/solve/jobs/{job_id}` | GET     | Poll process-local job execution and result               |

The former webapp-shaped routes for weights, wishes/blocked periods, minimum staffing, schedules/publication and `/solve/options` were removed: they translated canonical models into legacy UI formats. Their features return as canonical endpoints in later slices.

Next's `GET /api/health` makes a server-side request to API `/status`: it returns healthy only for a valid API liveness response, or `503` if the API is unavailable. Database availability is separate. Direct TimeOffice failures return `503` with sanitized `detail`, `integration: timeoffice` and the failed `stage`; accepted background jobs still report failures through their job state. See the [read-only diagnostic](../getting-started/installation.md#database-configuration).

## Selection and employee reads

`GET /planning/options?year=2026&month=1` returns the canonical `planning_month` (inclusive derived start/end) and named `planning_units` with station type. Only stations with a unique configured full-month target are offered. Empty options are distinct from a source failure.

`GET /employees?year=2026&month=1&planning_unit_ids=101&planning_unit_ids=102` accepts repeated positive station IDs and deduplicates them. The numbers here are illustrative, not connected target IDs. The response contains `selected_station_ids`, `planning_units` including relevant pool/home units, and deduplicated employees. Each employee has `employee_id`, `display_name`, `staff_level`, full dated `memberships`, `account`, `hard_restrictions` and `restrictions_source`. Accounts expose target/actual/credited minutes, dated `credit_details` and `evidence_source`. OpenAPI supplies the exact current schema. The retired `planning_unit`/`from_date` employee payload and split-name DTO are removed.

Invalid query values return `422`. Unavailable connectivity/query access returns sanitized `503`. Incomplete/ambiguous prepared facts or invalid station selection return `409` and no employee table. A pool cannot be selected as a station. These routes execute synchronous database reads in FastAPI's worker pool and never create tables, read demand, mutate output, load filesystem cases or invoke the solver. All-or-error source validation prevents partially successful station inspection.

The webapp uses a small server-only native-fetch boundary with `cache: no-store`, a ten-second request timeout, schema validation and scope matching. Browser URLs contain the canonical month/station selection; SQL connection details remain server-side.

## Solve lifecycle

`POST /solve/` accepts nonempty `planning_unit_ids`, `year`, `month` and `timeout` in seconds. The selected month is expanded to a full calendar month. An accepted request returns HTTP 202 with its job ID/status. An occupied solve lock returns HTTP 423. An unknown job ID returns HTTP 404.

The background task fetches and validates TimeOffice data, runs the solver and writes feasible compatibility exports to `data/`. Job execution states are `accepted`, `running`, `succeeded` and `failed`. A succeeded job contains a solution whose status must be inspected separately; job success does not imply feasibility or independent acceptance. Generation does not automatically publish to SQL Server.

Jobs/lock live in memory and disappear on restart or development reload. Use one API process. Polling exposes job state, not the imported frontend's old phase-progress protocol.

## Side effects and compatibility

Configuration writes and publication change the external database. Some configuration readers can create supplemental tables; see [TimeOffice](timeoffice.md). This reference intentionally does not provide a publication command before its pending scope/acceptance verification.

The old fetch/insert/delete routes, multi-solve, metadata endpoint and CLI entry points are not supplied by this API. Existing frontend DTO translations differ from canonical domain models. Consult [limitations](../validation/index.md) for remaining integration and quality gates.
