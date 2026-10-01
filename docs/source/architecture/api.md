# API

This reference describes inspected source definitions. Connected database behavior and complete user workflows require separate acceptance evidence; see [current limitations](../validation/index.md).

The FastAPI application is `api/app/main.py`. With Compose running, open <http://localhost:8000/docs> for interactive request/response schemas, or <http://localhost:8000/openapi.json> for OpenAPI. Schemas reflect the current checkout.

## Routes

Consult OpenAPI for exact bodies and responses.

| Route               | Methods | Current behavior                                          |
| ------------------- | ------- | --------------------------------------------------------- |
| `/status`           | GET     | Process liveness without a TimeOffice query               |
| `/planning/options` | GET     | Named stations with unique full-month targets             |
| `/employees`        | GET     | Complete canonical combined month/station/pool inspection |

Only these routes exist. The former webapp-shaped routes (weights, wishes/blocked periods, minimum staffing, schedules/publication, `/solve/options`) and the solve job routes were removed; generation, configuration and publication return as canonical endpoints in later slices.

Next's `GET /api/health` makes a server-side request to API `/status`: it returns healthy only for a valid API liveness response, or `503` if the API is unavailable. Database availability is separate. Direct TimeOffice failures return `503` with sanitized `detail`, `integration: timeoffice` and the failed `stage`; accepted background jobs still report failures through their job state. See the [read-only diagnostic](../getting-started/installation.md#database-configuration).

## Selection and employee reads

`GET /planning/options?year=2026&month=1` returns the canonical `planning_month` (inclusive derived start/end) and named `planning_units` with station type. Only stations with a unique configured full-month target are offered. Empty options are distinct from a source failure.

`GET /employees?year=2026&month=1&planning_unit_ids=101&planning_unit_ids=102` accepts repeated positive station IDs and deduplicates them. The numbers here are illustrative, not connected target IDs. The response contains `selected_station_ids`, `planning_units` including relevant pool/home units, and deduplicated employees. Each employee has `employee_id`, `display_name`, `staff_level`, full dated `memberships`, `account`, `hard_restrictions` and `restrictions_source`. Accounts expose target/actual/credited minutes, dated `credit_details` and `evidence_source`. OpenAPI supplies the exact current schema. The retired `planning_unit`/`from_date` employee payload and split-name DTO are removed.

Invalid query values return `422`. Unavailable connectivity/query access returns sanitized `503`. Incomplete/ambiguous prepared facts or invalid station selection return `409` and no employee table. A pool cannot be selected as a station. These routes execute synchronous database reads in FastAPI's worker pool and never create tables, read demand, mutate output, load filesystem cases or invoke the solver. All-or-error source validation prevents partially successful station inspection.

The webapp calls these routes from server components through `webapp/src/lib/api.ts` with a ten-second timeout. Browser URLs contain the canonical month/station selection; SQL connection details remain server-side.

## Side effects

The API performs no database writes. Selection and inspection reads never create tables. The demand and weights queries that could provision tables were deleted with the removed solve wiring.
