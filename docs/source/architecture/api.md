# API

This reference describes the source definitions. Executed live checks are listed under [current limitations](../validation/index.md).

The FastAPI application is `api/app/main.py`. With Compose running, open <http://localhost:8000/docs> for interactive request/response schemas, or <http://localhost:8000/openapi.json> for OpenAPI. Schemas reflect the current checkout.

## Routes

Consult OpenAPI for exact bodies and responses.

| Route                                | Methods     | Current behavior                                                                                     |
| ------------------------------------ | ----------- | ---------------------------------------------------------------------------------------------------- |
| `/status`                            | GET         | Process liveness without a TimeOffice query                                                          |
| `/planning/options`                  | GET         | Named stations with unique full-month targets                                                        |
| `/employees`                         | GET         | Complete canonical combined month/station/jumper pool inspection                                     |
| `/planning/employees`                | GET         | The selection's employees by ID and name, without monthly accounts                                   |
| `/availability`                      | GET         | One employee's month: native absences, availability, wishes and shifts                               |
| `/availability/{employee_id}/{date}` | PUT, DELETE | Replace or delete that employee's availability on that date                                          |
| `/wishes/{employee_id}/{date}`       | PUT, DELETE | Replace or delete that employee's wish on that date                                                  |
| `/demand`                            | GET, PUT    | Read or replace the dated staffing demand of one station month                                       |
| `/demand/pattern`                    | POST        | Expand a weekly pattern into the month's dated demand; saves nothing                                 |
| `/generation`                        | POST, GET   | Start a full-month generation; read the latest job                                                   |
| `/review`                            | GET         | The schedule under review with its check and readable tables                                         |
| `/review/import`                     | POST        | Validate an uploaded `input`/`result` pair and review it                                             |
| `/review/files/{name}`               | GET         | Download `input.json`, `result.json`, `schedule.csv`, `employees.csv`, `besetzung.csv` or `gaps.csv` |
| `/publication`                       | POST        | Publish the accepted schedule under review to its stations' targets                                  |
| `/publication`                       | DELETE      | Remove the published duties of the named stations' month                                             |

Next's `GET /api/health` calls API `/status` server-side: it is healthy only for a valid liveness response, otherwise `503`. Database availability is separate. Direct TimeOffice failures return `503` with sanitized `detail`, `integration: timeoffice` and the failed `stage`. See the [read-only diagnostic](../getting-started/installation.md#database-configuration).

## Selection and employee reads

`GET /planning/options?year=2026&month=1` returns the canonical `planning_month` (inclusive derived start/end) and named `planning_units` with station type. Only stations with a unique configured full-month target are offered. Empty options are distinct from a source failure.

`GET /employees?year=2026&month=1&planning_unit_ids=101&planning_unit_ids=102` accepts repeated positive station IDs and deduplicates them. The numbers here are illustrative, not connected target IDs. The response contains `selected_station_ids`, `planning_units` including relevant jumper pool/home units, the reference `shifts` (ID, code, type) that availability entries may allow, and deduplicated employees. Each employee has `employee_id`, `display_name`, `staff_level`, full dated `memberships`, `account` and `availability` (native absences plus project availability). Accounts expose target, actual and credited minutes and the dated `credit_details` they sum.

Invalid query values return `422`, as does an invalid selection: a jumper pool, an unconfigured unit or a station without a target plan for the month. Unavailable connectivity/query access returns sanitized `503`. Incomplete or ambiguous prepared facts return `409` and no employee table. `associated_jumper_pool_ids` lists the jumper pools that members of the selected stations call home; a replacement membership in a jumper pool is not an association. These routes run synchronous reads in FastAPI's worker thread pool. They never create tables, read demand, write output, load files or invoke the solver. All-or-error source validation prevents partially successful station inspection.

The webapp calls these routes from server components through `webapp/src/lib/api.ts` with a ten-second timeout. Browser URLs contain the canonical month/station selection; SQL connection details remain server-side.

## Monthly configuration

`GET /availability?employee_id=1&year=2026&month=1` returns `absences` (approved TimeOffice absences, read-only), `availability`, `wishes`, the month's `calendar` and the reference `shifts` (`shift_id`, `code`, `type`) for one employee month. `GET /planning/employees` takes the same station selection as `/employees` and returns only `employee_id` and `display_name`, so choosing an employee does not depend on complete monthly accounts. The employee needs a membership in a configured unit during the month.

`PUT /availability/{employee_id}/{date}` takes `availability_type` (`unavailable`, `vacation`, `training`, `free_day`, `available_only`), `shift_ids` (only and required for `available_only`) and an optional nonblank `reason`. `PUT /wishes/{employee_id}/{date}` takes `type` (`free_day`, `free_shift`, `preferred_day`, `preferred_shift`) and `shift_id` for the shift wishes. A PUT replaces the entry of exactly that employee and date and returns the saved entry; `DELETE` removes it and returns `204`, also when nothing was stored.

`GET /demand?planning_unit_id=101&year=2026&month=1` returns `demand` (`null` until the station month is saved once), the month's `calendar` (`date`, ISO `weekday`, NRW `public_holiday` name) and `shifts`. `PUT /demand` takes `planning_unit_id`, `planning_month` (`year`, `month`) and the complete `cells` (`date`, `shift_id`, `staff_level`, `required_count` from 1 to 99); the station is given once. It replaces that station month; an empty list saves "nobody required". `POST /demand/pattern` takes the same station and month plus pattern `cells` (`day_type` `monday`…`sunday` or `holiday`, `shift_id`, `staff_level`, `required_count` from 0 to 99). It checks the station and shifts like a save and returns the resulting `MonthlyDemand` without saving it.

Malformed bodies, non-integer or out-of-range counts, an employee without membership, non-reference shifts, out-of-month or duplicate demand, jumper pools and stations without a target plan return `422` before any write. Incomplete source facts return `409`; unavailable TimeOffice returns sanitized `503`. Writes report success only after commit.

## Generation

`POST /generation` takes `planning_unit_ids` (at least one station), `planning_month` (`year`, `month`) and `timeout_seconds` (30 to 3600; the total CP-SAT search limit of all objective stages). It reads and validates the whole month's input synchronously, then returns `202` with the running job while the solve continues in a background thread. Before any job exists it returns `422` for invalid bodies and selections (jumper pools, stations without a target plan), `409` for incomplete input (a station without saved demand, incomplete employee facts, missing shift times), sanitized `503` when TimeOffice is unavailable, and `423` while another generation runs.

`GET /generation` returns the latest job since the API process started, or `404` when there is none, also after a restart. A job has `job_id`, the `request`, `state` (`running`, `completed`, `failed`), `started_at`/`finished_at`, and either `solution` (when completed) or a generic `error` (when failed; the exception is logged, not returned). `solution` carries the CP-SAT `status` (`optimal`, `feasible`, `infeasible`, `model_invalid`, `unknown`), the effective `configuration` (rule policy, timeout, workers, seed), `wall_time_seconds` and `diagnostics`. With a found schedule it also has (see [solver result](solver.md#result)):

- `assignments`: `employee_id`, `date`, `planning_unit_id`, `shift_id`, credited `staff_level`
- `gaps`: station, date, shift, qualification, `missing_count`
- `stages`: per objective tier `name`, `status`, `value`, `best_bound`; `null` for a stage that found no schedule in its time
- `check`: the independent check with `status` (`accepted`, `rejected`, `incomplete`), `findings`, `not_assessed`, `scores`, `wishes` with their outcomes and `wish_counts`

`completed` with `infeasible` is a finished job without a schedule.

The input is the `SchedulingDataset` from `TimeOfficeService.read_generation_input`: the selection's employee inspection, the reference shifts from `TDiensteSollzeiten`, each station's saved demand and the [trusted context](timeoffice.md#read-and-write-boundaries) around the month. Units are the selected stations and their associated jumper pools. Worked roster rows enter only from trusted context plans outside the month, so earlier output in the target plan never becomes input. Project wishes of every inspected employee, jumper pool members included, are input; native TimeOffice wish rows are not.

One `Generation` object (`api/app/solver/generation.py`) owns the process-local lock, the single background worker and the latest job; the lock is released on success and failure. Jobs are not persisted. Run one API process.

## Review, import and download

One `Review` object (`api/app/solver/review.py`) holds the schedule under review in memory: every generation that finds a schedule replaces it before its job reports `completed`, and so does a valid import. A generation without a schedule and a rejected import leave it unchanged; a restart forgets it.

`GET /review` returns `404` without a schedule, otherwise `source` (`generation`, `import`), `received_at`, the `planning_month`, `planning_units`, `shifts` and `calendar` of the input, the `solution` and `tables`: `duties`, `employees`, `staffing` (required against assigned count per station, date, shift and qualification) and `gaps` (the staffing rows with missing slots, with station name and shift code). The duty, employee and gap rows are the rows of the CSV files.

`POST /review/import` takes multipart files `input` and `result`. It returns the new review, or `422` with `detail` and `problem`: `malformed` (not JSON, schema violation, unknown field, other format version or calendar), `mismatch` (the result names another input digest or month), `no_schedule`, `policy` (solved with other rule settings), `references` (assignments of unknown employees, stations or shifts, outside the month or duplicated) or `check` (a stored check that differs from the independent re-check). Validation runs in the worker thread pool.

`GET /review/files/{name}` returns the file as an attachment (`application/json` or `text/csv; charset=utf-8`), or `404` without a schedule. `input.json` keeps the exact bytes its digest names. The format is described under [bundle files](../validation/examples.md#bundle-files); `ScheduleBundle` (`api/app/solver/bundle.py`) owns parsing, pairing, re-checking and rendering, so imports, downloads and the [example tests](../validation/examples.md#validate-monthly-and-sequence-results) share one implementation. A generated schedule becomes a bundle directly with the solver's check; only uploaded pairs are re-validated.

## Publication and clear

`POST /publication` takes `planning_month` (`year`, `month`), `planning_unit_ids` and `received_at` of the schedule under review, as `GET /review` returned them. The route takes the assignments only from `Review.publishable`; only then does `TimeOfficeService.publish` write. After commit, the response names the month and stations, `removed_duties` (the replaced earlier publication) and `published_duties` (written and read back).

| Response                | Cause                                                                                                  |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| `409` `changed`         | No schedule under review, or it differs in arrival, month or stations                                  |
| `409` `not_accepted`    | The schedule's check is not `accepted`                                                                 |
| `409` `conflict`        | An employee has an absence or another duty (entered in TimeOffice or in another plan) on a duty's date |
| `409` `read_back`       | The written duties read back differently                                                               |
| `409` `concurrent`      | A concurrent writer or an existing row collided; applies to every write route                          |
| `409` without `problem` | Ambiguous targets, a qualification no station membership books, or incomplete shift data               |
| `422`                   | A schedule without duties, or duties outside the named stations or month                               |
| `503`                   | TimeOffice failed; with stage `commit` the connection failed while committing                          |

Every failure rolls the transaction back, except a `503` with stage `commit`, whose outcome is unknown.

`DELETE /publication?year=2026&month=1&planning_unit_ids=101` takes the same repeated station IDs as `/employees` and returns the same result with `published_duties` 0. Jumper pools and stations without a target plan return `422`. Publication and clear run one at a time in the API process; see [TimeOffice publication](timeoffice.md#publication) for the transaction.

The webapp waits up to two minutes for either write, adds _Nichts wurde geändert_ to a rolled-back failure, and reports an unanswered request or a failed commit as an unknown outcome.

## Side effects

The configuration PUT/DELETE routes write the [project tables](timeoffice.md#project-tables); `POST` and `DELETE /publication` write the marked duty rows of the named stations' target plans. Generation, review and import write nothing; downloads are rendered in memory. No route creates tables or writes plan, account, absence or wish rows.
