# API

This reference describes inspected source definitions. Connected database behavior and complete user workflows require separate acceptance evidence; see [current limitations](../validation/index.md).

The FastAPI application is `api/app/main.py`. With Compose running, open <http://localhost:8000/docs> for interactive request/response schemas, or <http://localhost:8000/openapi.json> for OpenAPI. Schemas reflect the current checkout.

## Routes

Consult OpenAPI for exact bodies and responses.

| Route                                | Methods     | Current behavior                                                       |
| ------------------------------------ | ----------- | ---------------------------------------------------------------------- |
| `/status`                            | GET         | Process liveness without a TimeOffice query                            |
| `/planning/options`                  | GET         | Named stations with unique full-month targets                          |
| `/employees`                         | GET         | Complete canonical combined month/station/jumper pool inspection       |
| `/planning/employees`                | GET         | The selection's employees by ID and name, without monthly accounts     |
| `/availability`                      | GET         | One employee's month: native absences, availability, wishes and shifts |
| `/availability/{employee_id}/{date}` | PUT, DELETE | Replace or delete that employee's availability on that date            |
| `/wishes/{employee_id}/{date}`       | PUT, DELETE | Replace or delete that employee's wish on that date                    |
| `/demand`                            | GET, PUT    | Read or replace the dated staffing demand of one station month         |
| `/demand/pattern`                    | POST        | Expand a weekly pattern into the month's dated demand; saves nothing   |
| `/generation`                        | POST, GET   | Start a full-month generation; read the latest job                     |

Review and publication have no endpoints yet.

Next's `GET /api/health` makes a server-side request to API `/status`: it returns healthy only for a valid API liveness response, or `503` if the API is unavailable. Database availability is separate. Direct TimeOffice failures return `503` with sanitized `detail`, `integration: timeoffice` and the failed `stage`. See the [read-only diagnostic](../getting-started/installation.md#database-configuration).

## Selection and employee reads

`GET /planning/options?year=2026&month=1` returns the canonical `planning_month` (inclusive derived start/end) and named `planning_units` with station type. Only stations with a unique configured full-month target are offered. Empty options are distinct from a source failure.

`GET /employees?year=2026&month=1&planning_unit_ids=101&planning_unit_ids=102` accepts repeated positive station IDs and deduplicates them. The numbers here are illustrative, not connected target IDs. The response contains `selected_station_ids`, `planning_units` including relevant jumper pool/home units, and deduplicated employees. Each employee has `employee_id`, `display_name`, `staff_level`, full dated `memberships`, `account` and `availability` (native absences plus project availability). Accounts expose target/actual/credited minutes, dated `credit_details` and `evidence_source`. OpenAPI supplies the exact current schema. The retired `planning_unit`/`from_date` employee payload and split-name DTO are removed.

Invalid query values return `422`, as does an invalid selection: a jumper pool, an unconfigured unit or a station without a target plan for the month. Unavailable connectivity/query access returns sanitized `503`. Incomplete or ambiguous prepared facts return `409` and no employee table. `associated_jumper_pool_ids` lists the jumper pools that members of the selected stations call home; a replacement membership in a jumper pool is not an association. These routes execute synchronous database reads in FastAPI's worker jumper pool and never create tables, read demand, mutate output, load filesystem cases or invoke the solver. All-or-error source validation prevents partially successful station inspection.

The webapp calls these routes from server components through `webapp/src/lib/api.ts` with a ten-second timeout. Browser URLs contain the canonical month/station selection; SQL connection details remain server-side.

## Monthly configuration

`GET /availability?employee_id=1&year=2026&month=1` returns `absences` (approved TimeOffice absences, read-only), `availability`, `wishes`, the month's `calendar` and the reference `shifts` (`shift_id`, `code`, `type`) for one employee month. `GET /planning/employees` takes the same station selection as `/employees` and returns only `employee_id` and `display_name`, so choosing an employee does not depend on complete monthly evidence. The employee needs a membership in a configured unit during the month.

`PUT /availability/{employee_id}/{date}` takes `availability_type` (`unavailable`, `vacation`, `training`, `free_day`, `available_only`), `shift_ids` (only and required for `available_only`) and an optional nonblank `reason`. `PUT /wishes/{employee_id}/{date}` takes `type` (`free_day`, `free_shift`, `preferred_day`, `preferred_shift`) and `shift_id` for the shift wishes. A PUT replaces the entry of exactly that employee and date and returns the saved entry; `DELETE` removes it and returns `204`, also when nothing was stored.

`GET /demand?planning_unit_id=101&year=2026&month=1` returns `demand` (`null` until the station month is saved once), the month's `calendar` (`date`, ISO `weekday`, NRW `public_holiday` name) and `shifts`. `PUT /demand` takes `planning_unit_id`, `planning_month` (`year`, `month`) and the complete `cells` (`date`, `shift_id`, `staff_level`, `required_count` from 1 to 99); the station is given once. It replaces that station month; an empty list saves "nobody required". `POST /demand/pattern` takes the same station and month plus pattern `cells` (`day_type` `monday`…`sunday` or `holiday`, `shift_id`, `staff_level`, `required_count` from 0 to 99). It checks the station and shifts like a save and returns the resulting `MonthlyDemand` without saving it.

Malformed bodies, non-integer or out-of-range counts, an employee without membership, non-reference shifts, out-of-month or duplicate demand, jumper pools and stations without a target plan return `422` before any write. Incomplete source facts return `409`; unavailable TimeOffice returns sanitized `503`. Writes report success only after commit.

## Generation

`POST /generation` takes `planning_unit_ids` (at least one station), `planning_month` (`year`, `month`) and `timeout_seconds` (greater than 0, at most 3600; the CP-SAT search limit). It reads and validates the whole month's input synchronously, then returns `202` with the running job while the solve continues in a background thread. Before any job exists it returns `422` for invalid bodies and selections (jumper pools, stations without a target plan), `409` for incomplete input (a station without saved demand, incomplete employee facts, missing shift times), sanitized `503` when TimeOffice is unavailable, and `423` while another generation runs.

`GET /generation` returns the latest job since the API process started, or `404` when there is none, also after a restart. A job has `job_id`, the `request`, `state` (`running`, `completed`, `failed`), `started_at`/`finished_at`, and either `solution` (when completed) or a generic `error` (when failed; the exception is logged, not returned). `solution` carries the CP-SAT `status` (`optimal`, `feasible`, `infeasible`, `model_invalid`, `unknown`), the generated `assignments` (`employee_id`, `planning_unit_id`, `date`, `shift_id`), `diagnostics` and `audit` findings. `completed` with `infeasible` is a finished job without a schedule. `acceptance` is always `not_assessed`: no independent schedule check exists yet.

The input is the `SchedulingDataset` built by `TimeOfficeService.read_generation_input`: the employee inspection of the selection, the reference shifts with times and paid minutes from `TDiensteSollzeiten`, and the saved demand of each selected station. Units are the selected stations and their associated jumper pools. Roster rows are read only as approved absences; worked shifts of any plan, including earlier output in the target plan, never become input. Wishes, existing or boundary assignments and plans are left empty.

One `Generation` object (`api/app/solver/generation.py`) owns the process-local lock, the single background worker and the latest job; the lock is released on success and failure. Jobs are not persisted. Run one API process.

## Side effects

Only the configuration PUT/DELETE routes write, and only to the [project tables](timeoffice.md#project-tables). Generation writes nothing. No route creates tables or writes TimeOffice roster, plan or account rows.
