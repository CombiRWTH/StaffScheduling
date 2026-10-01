# API

This reference describes inspected source definitions. Connected database behavior and complete user workflows require separate acceptance evidence; see [current limitations](../validation/index.md).

The FastAPI application is `api/app/main.py`. With Compose running, open <http://localhost:8000/docs> for interactive request/response schemas, or <http://localhost:8000/openapi.json> for OpenAPI. Schemas reflect the current checkout.

## Routes

Configuration routes use `planning_unit` and `from_date` query parameters; consult OpenAPI for exact bodies and responses.

| Route                               | Methods     | Current behavior                                                                               |
| ----------------------------------- | ----------- | ---------------------------------------------------------------------------------------------- |
| `/status`                           | GET         | Process liveness without a TimeOffice query                                                    |
| `/employees`                        | GET         | Read employees for a unit/month                                                                |
| `/weights`                          | GET, PUT    | Read/update objective weights                                                                  |
| `/wishes-and-blocked`               | GET         | Read wishes and availability                                                                   |
| `/wishes-and-blocked/{employee_id}` | PUT, DELETE | Replace/delete employee wishes and blocked periods                                             |
| `/minimal-staff`                    | GET, PUT    | Read/update minimum staffing                                                                   |
| `/schedules`                        | GET         | Empty placeholder list                                                                         |
| `/schedules/write-to-timeoffice`    | POST        | Translate submitted legacy variables and write assignments; scope/acceptance hardening pending |
| `/solve/options`                    | GET         | Read selectable planning units                                                                 |
| `/solve/`                           | POST        | Accept a full-month solve job                                                                  |
| `/solve/jobs/{job_id}`              | GET         | Poll process-local job execution and result                                                    |

Next's `GET /api/health` makes a server-side request to API `/status`: it returns healthy only for a valid API liveness response, or `503` if the API is unavailable. Database availability is separate. Direct TimeOffice failures return `503` with sanitized `detail`, `integration: timeoffice` and the failed `stage`; accepted background jobs still report failures through their job state. See the [read-only diagnostic](../getting-started/installation.md#database-configuration).

## Solve lifecycle

`POST /solve/` accepts nonempty `planning_unit_ids`, `year`, `month` and `timeout` in seconds. The selected month is expanded to a full calendar month. An accepted request returns HTTP 202 with its job ID/status. An occupied solve lock returns HTTP 423. An unknown job ID returns HTTP 404.

The background task fetches and validates TimeOffice data, runs the solver and writes feasible compatibility exports to `data/`. Job execution states are `accepted`, `running`, `succeeded` and `failed`. A succeeded job contains a solution whose status must be inspected separately; job success does not imply feasibility or independent acceptance. Generation does not automatically publish to SQL Server.

Jobs/lock live in memory and disappear on restart or development reload. Use one API process. Polling exposes job state, not the imported frontend's old phase-progress protocol.

## Side effects and compatibility

Configuration writes and publication change the external database. Some configuration readers can create supplemental tables; see [TimeOffice](timeoffice.md). This reference intentionally does not provide a publication command before its pending scope/acceptance verification.

The old fetch/insert/delete routes, multi-solve, metadata endpoint and CLI entry points are not supplied by this API. Existing frontend DTO translations differ from canonical domain models. Consult [limitations](../validation/index.md) for remaining integration and quality gates.
