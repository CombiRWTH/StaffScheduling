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

Only these routes exist. Configuration, generation, review and publication have no endpoints yet.

Next's `GET /api/health` makes a server-side request to API `/status`: it returns healthy only for a valid API liveness response, or `503` if the API is unavailable. Database availability is separate. Direct TimeOffice failures return `503` with sanitized `detail`, `integration: timeoffice` and the failed `stage`. See the [read-only diagnostic](../getting-started/installation.md#database-configuration).

## Selection and employee reads

`GET /planning/options?year=2026&month=1` returns the canonical `planning_month` (inclusive derived start/end) and named `planning_units` with station type. Only stations with a unique configured full-month target are offered. Empty options are distinct from a source failure.

`GET /employees?year=2026&month=1&planning_unit_ids=101&planning_unit_ids=102` accepts repeated positive station IDs and deduplicates them. The numbers here are illustrative, not connected target IDs. The response contains `selected_station_ids`, `planning_units` including relevant pool/home units, and deduplicated employees. Each employee has `employee_id`, `display_name`, `staff_level`, full dated `memberships`, `account`, `hard_restrictions` and `restrictions_source`. Accounts expose target/actual/credited minutes, dated `credit_details` and `evidence_source`. OpenAPI supplies the exact current schema. The retired `planning_unit`/`from_date` employee payload and split-name DTO are removed.

Invalid query values return `422`, as does an invalid selection: a pool, an unconfigured unit or a station without a target plan for the month. Unavailable connectivity/query access returns sanitized `503`. Incomplete or ambiguous prepared facts return `409` and no employee table. `associated_pool_ids` lists the pools that members of the selected stations call home; a replacement membership in a pool is not an association. These routes execute synchronous database reads in FastAPI's worker pool and never create tables, read demand, mutate output, load filesystem cases or invoke the solver. All-or-error source validation prevents partially successful station inspection.

The webapp calls these routes from server components through `webapp/src/lib/api.ts` with a ten-second timeout. Browser URLs contain the canonical month/station selection; SQL connection details remain server-side.

## Side effects

The API performs no database writes. Selection and inspection reads never create tables.
