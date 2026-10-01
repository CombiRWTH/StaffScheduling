# API reference

The FastAPI application is `api/app/main.py`. Run `just api-dev` from the repository root, then inspect the actual schemas at `http://localhost:8000/docs` or `/openapi.json`.

## Routes

This inventory was checked against the relocated application's OpenAPI schema. Configuration routes take the query parameters `planning_unit` and `from_date`; refer to OpenAPI for request and response schemas.

| Route                               | Methods     | Behavior                                                                                                                   |
| ----------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------- |
| `/status`                           | GET         | Process liveness; does not query TimeOffice.                                                                               |
| `/employees`                        | GET         | Read employees for a planning unit and month.                                                                              |
| `/weights`                          | GET, PUT    | Read or update objective weights.                                                                                          |
| `/wishes-and-blocked`               | GET         | Read wishes and availability.                                                                                              |
| `/wishes-and-blocked/{employee_id}` | PUT, DELETE | Replace or delete employee wishes and blocked periods.                                                                     |
| `/minimal-staff`                    | GET, PUT    | Read or update staffing demand.                                                                                            |
| `/schedules`                        | GET         | Current placeholder returns an empty schedule list.                                                                        |
| `/schedules/write-to-timeoffice`    | POST        | Convert submitted legacy variables to domain assignments and write to TimeOffice; scoped publication hardening is pending. |
| `/solve/options`                    | GET         | Read available planning units.                                                                                             |
| `/solve/`                           | POST        | Start a full-month solve job.                                                                                              |
| `/solve/jobs/{job_id}`              | GET         | Poll a transient solve job.                                                                                                |

## Generation

The solve router fetches a canonical dataset from TimeOffice, validates it and runs the CP-SAT solver asynchronously. One process-local lock prevents concurrent solves. Jobs and their results are transient and disappear on restart; use one API worker.

Generation uses the HTTP API and requires TimeOffice data. The obsolete command-line entry point and historical case directories have been removed.

## Compatibility and limits

The imported frontend also expects legacy fetch/insert/delete, phase-based progress, multi-solve and schedule metadata/file operations. Those are not supplied by this API inventory. See [webapp integration limits](../webapp/solver-integration.md) before using those views.

The relocated source preserves existing adapter and solver behavior. `/status` and valid OpenAPI schemas do not establish database access, schedule feasibility, independent acceptance or safe publication. Configuration/TLS and independent connectivity diagnostics follow in the foundation pass; domain and scoped write changes follow in their feature slices.
