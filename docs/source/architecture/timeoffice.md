# TimeOffice adapter

This reference describes the adapter and the prepared test database. Executed live checks are listed under [current limitations](../validation/index.md).

`api/app/timeoffice/` owns the application's Microsoft SQL Server integration. `TimeOfficeService` coordinates queries, their translation into canonical models, scoped writes to the project tables and the publication of schedules into target plans. The solver depends on the [domain model](domain.md), not the database schema.

## Modules

| Path under `api/app/timeoffice/` | Responsibility                                                                                                                                                                          |
| -------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `database.py`                    | SQLAlchemy engine using `mssql+pyodbc`                                                                                                                                                  |
| `facts.py`                       | Configured units, reference shifts, account IDs, code mappings and planning status                                                                                                      |
| `queries.py`                     | One function per TimeOffice SELECT, returning canonical models with its code/account translation; `read_accounts` adds its private daily-credit SELECT so callers get complete accounts |
| `project_tables.py`              | Reads and key-scoped writes of the project tables next to the TimeOffice schema                                                                                                         |
| `roster.py`                      | Publication's roster statements: validated duty rows, read-back, replacement and clear of the target plans' worked rows                                                                 |
| `service.py`                     | `TimeOfficeService`, the package's only public entry point; one connection per call                                                                                                     |

## Connection and schema

Follow [database configuration](../getting-started/installation.md#database-configuration) for `.env` and the password file. Docker includes ODBC Driver 18. `database.py` constructs the SQLAlchemy URL with `Encrypt=yes` and verifies the server certificate (`TrustServerCertificate=no`) unless `DB_TRUST_SERVER_CERTIFICATE=true`. Its shared connection boundary checks missing configuration/driver, applies bounded login/query waits, and translates driver failures into safe integration errors for all adapter callers. FastAPI returns these as `503` with `integration`, `stage` and actionable `detail`; liveness remains independent. No connection strings, SQL or raw driver errors are returned.

`just connectivity` runs the explicit diagnostic in the API container. It checks configuration/ODBC/DNS, encrypted login and `SELECT 1`, then disposes the engine. It bypasses all application queries. Offline boundary checks cover missing configuration, missing driver, sanitized login/query failures and a simulated successful diagnostic. The configured test server presents a self-signed certificate; with `DB_TRUST_SERVER_CERTIFICATE=true` all diagnostic stages pass and live read-only queries succeed. On the test database the project tables and the [prepared example units](#prepared-example-units) exist; the live checks run against them are listed under [current limitations](../validation/index.md#webapp-integration). See [testing](../development/testing.md).

The adapter reads TimeOffice tables including `TPlanungseinheiten`, `TPlanungseinheitenPersonal`, `TPersonal`, `TPlan`, `TDienste`, `TPlanPersonalKommtGeht` and monthly/daily account tables. Actual SQL and join/filter rules are in `queries.py`; this reference does not substitute a copied schema diagram for the database's current schema.

## Read and write boundaries

`TimeOfficeService` is the adapter's whole interface: `get_planning_options`, `inspect_employees`, `list_employees`, `get_employee_calendar`, `set_availability`, `set_wish` (an entry replaces, `None` removes), `get_demand`, `save_demand`, `preview_demand`, `read_generation_input`, `publish` and `clear` take canonical arguments and return canonical domain models. SQL, source rows and TimeOffice terminology stay private to the package (`app.timeoffice` exports only the service, the unavailable error and the engine factory). Each query function translates its own source codes and checks source-level facts such as missing master rows, duplicate target plans or unmapped codes; cross-entity completeness belongs to `domain/inspection.py`. Each router declares the small protocol it needs (`PlanningSource`, `AvailabilitySource`, `DemandSource`, `PublicationTarget`), so another planning database can replace TimeOffice without touching routes or domain, and a new feature adds its own protocol instead of growing a shared one. TimeOffice reductions and fixed reference mappings in `facts.py` remain adapter behavior and must be checked against the chosen data.

The adapter writes the project tables and, through `publish` and `clear`, the worked rows of the target plans. `read_generation_input` builds the solver's `SchedulingDataset` from the employee inspection, the reference shifts, the saved demand and the trusted context. Each reference shift's `TDiensteSollzeiten` rows are its work segments (an overnight segment ends on the next day). A segment's `Minuten` equals its length, so paid time is worked time; the gaps between segments are unpaid breaks: F 05:55–13:25 has 30 minutes (420 paid), Z 08:30–14:15 none (345), S 13:15–21:00 30 minutes (435) and N 20:10–06:10 15 + 30 minutes (555).

Trusted context comes from plans with status 30 (`TRUSTED_CONTEXT_STATUS_ID`) of the configured stations. `read_context_coverage` finds the dates within the 5 days before and 3 days after the month that the rules reach (`RulePolicy`) and that such a plan of every configured station spans; the context covers the gap-free run of those dates next to the month. `read_context_duties` reads their worked rows and groups them per employee and date; the segments must reproduce a reference shift's catalog segments on that date, otherwise the read fails. A context duty inside the month fails too, because fixed in-month input is not supported. Absences and project availability of the first date after the month complete the context. All other roster rows are read only as approved absences, so published output in the target plan never becomes generation input. Publishing into a status-20 target therefore does not make it context for the next month; trusted context stays in status-30 plans.

## Monthly accounts and credits

Selection and employee inspection are strictly read-only. They never create tables, nor do they require `TPlanPersonal` or existing work duties in an empty target. Target plans are selected internally by configured status/interval and exact month bounds. Memberships across the configured units determine jumper pool/home context; jumper pool origin alone is never destination eligibility. Missing names, identities, unique targets or accounts fail inspection.

`read_accounts` returns each employee's complete `MonthlyWorkAccount` from native TimeOffice accounts:

| Value          | Source                                                              | Rule                                         |
| -------------- | ------------------------------------------------------------------- | -------------------------------------------- |
| Target minutes | `TPersonalKontenJeMonat`, account 1 (`SOLL_MONAT`), `Wert2` hours   | Required; explicit zero is kept              |
| Actual minutes | `TPersonalKontenJeMonat`, account 55 (`TOTAL`), `Wert2` hours       | Optional; never treated as a credit          |
| Dated credits  | `TPersonalKontenJeTag` absence-hour accounts, `Wert` hours per date | Each row must fall on an absence of its code |

`docs/adr/0008-credits-from-timeoffice-daily-absence-accounts.md` records why. The credit accounts are 85 `U_STD` (vacation, code `U`), 93 `FI_STD` (internal training, `FI`), 95 `FE_STD` (external training, `FE`) and 97 `ST_STD` (school, `SC`). TimeOffice books these per date, and its monthly account of the same number is their sum. It books a credited absence on every Monday-to-Friday date that is not an NRW public holiday and none on weekends or holidays. A credit row on a date without a roster absence of its code rejects the inspection, and so does a credited absence on such a weekday without its booking. On a weekend or holiday an absence credits nothing. The check uses the absences `read_absences` returns, so both reads share one definition of a roster absence. A unit whose employees work fewer than five days a week would need a different booking rule; it fails this check rather than being credited wrongly. Each credit becomes an `approved_absence` `WorkCredit` with source `TimeOffice <code> absence`. Native absences are loaded separately and keep their reason; project availability comes from its own table. Unknown shifts and ambiguous home origin reject the complete inspection as well.

## Project tables

An authorized preparer runs `api/sql/supplemental-tables.sql` once in the declared database. It creates `dbo.StaffSchedulingAvailability`, `dbo.StaffSchedulingWish`, `dbo.StaffSchedulingDemandMonth` and `dbo.StaffSchedulingDemand`. Creating them needs DDL permission; the runtime login needs SELECT, INSERT and DELETE on all four. The API never creates tables. Without them, live inspection, configuration and generation fail with a query-stage `503`. On the test database they exist; its single login holds `db_ddladmin`, `db_datareader` and `db_datawriter`, so setup and runtime privileges are not separated there.

| Table                         | Key                                 | Meaning                                                                    |
| ----------------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| `StaffSchedulingAvailability` | employee, date                      | Canonical availability type, JSON `shift_ids` for `available_only`, reason |
| `StaffSchedulingWish`         | employee, date                      | Canonical wish type and optional shift                                     |
| `StaffSchedulingDemandMonth`  | station, first of month             | The station month's demand has been saved                                  |
| `StaffSchedulingDemand`       | station, date, shift, qualification | Required count ≥ 1; a missing row in a saved month requires nobody         |

Employee inspection also reads `StaffSchedulingAvailability`, so the Mitarbeiter page needs these tables too. Every write runs in one transaction and validates first: the employee needs a membership in a configured unit that month (a single scoped membership query), shifts must be reference shifts, and a demand station needs a target plan. An availability or wish save deletes and inserts exactly one employee date; a demand save replaces exactly one station month and marks it saved. Writes need no target-plan rows, roster rows or profession lookups, so they also work on empty prepared targets. Serialize writes as for every shared database change. `docs/adr/0006-monthly-configuration-in-project-tables.md` records why these tables are used instead of native TimeOffice wish rows or the old recurring `StaffSchedulingMinimalStaffing` table, which the API no longer reads.

Intentional mappings: project availability and wishes are invisible in TimeOffice, and native TimeOffice wishes (`Wunschdienst` rows) are not read. Reference shifts are the four facts in `facts.py` (F `1113`, Z `1453`, S `1605`, N `1690`); their codes come from `TDienste`, their types from the facts. Staff levels and availability types are stored as their canonical values.

## Publication

`publish` writes a reviewed schedule into the selected stations' target plans for the month; `clear` removes it. The route takes the assignments from `Review.publishable` (`api/app/solver/review.py`), which yields only the accepted schedule under review, so the adapter receives canonical assignments and the station scope, never plan IDs. `docs/adr/0009-publish-marked-duties-into-timeoffice-target-plans.md` records the decision. The published output of a target plan is its worked rows (no absence code in `RefgAbw`/`RefDienstAbw`, no `Wunschdienst`) marked with `Info` = `StaffScheduling` (`GENERATED_DUTY_INFO`). Publication replaces exactly those rows of the named stations' target plans; absences, native wishes, duties entered in TimeOffice, other plans and every other station month are kept.

Inside one transaction, before anything is deleted, `publish`:

1. selects each station's single target plan with the rule `read_target_plans` shares with every read; a missing target is `422`, several fail with `409`,
2. checks that every duty belongs to a named station and the month, uses a reference shift, and is the employee's only duty that date,
3. finds the profession (`RefBerufe`) of the employee's active membership at that station whose mapped qualification equals the duty's credited qualification, and fails unless there is exactly one,
4. reads the employees' kept roster rows of the month and refuses (`conflict`) a duty on a date with an absence or a worked row outside the replaced output, for example an absence entered after generation, a duty entered in TimeOffice in the target plan or a duty in another plan,
5. counts and deletes the old output, inserts the new rows, reads them back as canonical duties and rolls back (`read_back`) unless they equal the schedule.

Only then does it commit. Any failure rolls back the deletion as well. Publication and clear hold a process lock and run in a `SERIALIZABLE` transaction, so a concurrent writer from another process makes one of them fail and roll back rather than interleave target checks and row numbers. The engine translates such collisions (a deadlock victim, SQL Server error 1205 or SQLSTATE `40001`, and a duplicate key, errors 2627 and 2601, read from the driver message) into `TimeOfficeConflict`, which the API returns as `409` with `problem` `concurrent`; other driver failures, including foreign-key or NOT NULL violations, stay sanitized `503`s. The commit runs separately: a failure of the commit itself returns `503` with stage `commit`, because the change may or may not have been saved. Run one API process. Multi-row inserts use pyodbc's `fast_executemany` for every write of the engine, demand saves included; a month publishes in about a second.

A duty is stored as TimeOffice stores worked duties: one `TPlanPersonalKommtGeht` row per catalog segment of its reference shift, with the duty's start date as `Datum` (a night's last segment ends on the next day), the segment's wall-clock `VonZeit`/`BisZeit` and `Minuten` (their sum is the shift's paid minutes; on a clock-change night the elapsed time differs by an hour), row status 20, the profession from step 3, the station as `RefPlanungseinheiten` and `RefPeinheitOwner`, also for a jumper pool employee, and the `Info` marker. Because the roster key `(RefPersonal, Datum, RefStati, lfdNr)` excludes the plan, the segments are numbered after the employee's kept rows of that row status on the date; with no such row they are 1..n. A native wish on the date therefore keeps its number.

Intentional reductions and limits: source detail beyond the reference shift's segments is not written (no deployment type or readiness times), and reading back accepts only rows that reproduce a reference shift. Planners must not put the marker text into `Info` of their own duties. No `TPlanPersonal` rows are created; the prepared plans have none, and whether the TimeOffice client lists published employees without them is not verified. A conflict names the employee and date in the API's `detail`. The runtime login needs SELECT, INSERT and DELETE on `TPlanPersonalKommtGeht` in addition to the reads; the test login's `db_datawriter` role covers this.

## Prepared example units

The test database holds a fictional example scope for January–June 2026, created by additive SQL. Existing units, employees and rosters are unchanged. Every prepared row is identified by its `BSP` business key (Beispiel), so it can be removed again in reverse dependency order.

| Unit (`KurzBez`) | `Prim` | Role                                            |
| ---------------- | ------ | ----------------------------------------------- |
| `BSP-A`          | 427    | Station with demand profile 85                  |
| `BSP-B`          | 428    | Station with demand profile 79                  |
| `BSP-JUMP`       | 429    | Jumper pool (`IstPoolPlanungseinheit`) for both |

`facts.py` configures only these three units. The population, contracts, absences and boundary context are described in [examples and reproduction](../validation/examples.md#input-data-and-boundary-context). Native facts that later work depends on:

- Each station month has one target plan (status 20, interval 1, exact month bounds), empty of worked rows until a schedule is published. Jumper pool absences sit in jumper pool plans of the same form; the jumper pool is never selectable.
- Trusted boundary duties for 2025-12-18..31 and 2026-07-01..07 are worked roster rows in approved station plans (status 30) spanning December 2025 and July 2026. Generation reads them as context; a context plan is complete for every date it spans.
- A worked duty is one roster row per `TDiensteSollzeiten` segment (`lfdNr` 1..n, paid `Minuten` per segment). An absence row sets `RefgAbw` and `RefDienstAbw` to the absence code and `Minuten` to 0.
- The roster primary key is `(RefPersonal, Datum, RefStati, lfdNr)` and does not include the plan. An employee therefore has at most one row set per date and row status across all plans, absences included.
- `TPersonal.PersNr`, `MagnetKarte` and `IdentifikationMAPortal` are unique; the prepared employees use the staff number for all three.

## Supporting another unit

To plan an existing TimeOffice unit, check each item with read-only queries first, then add the unit to `planning_unit_type_by_id` in `facts.py`:

1. **Unit.** Monthly interval (`RefPlanungsIntervalle` 1); decide whether it is a station or a jumper pool.
2. **Target plans.** Exactly one plan per planned month with status 20, interval 1 and exact month bounds. Generation ignores worked rows already in it; [publication](#publication) replaces them.
3. **Memberships.** Every `TPlanungseinheitenPersonal` row of the unit that overlaps a planned month (`KeinEPlan` 0) needs a profession mapped in `STAFF_LEVEL_BY_PROFESSION_CODE`. Each employee needs exactly one home unit (`IstHeimat`) on every active date. Jumper pool staff need replacement memberships at the stations they may cover.
4. **Employees.** A name and a mapped profession in `TPersonal`.
5. **Accounts.** A target (account 1) for every employee and planned month.
6. **Absences and credits.** Every absence code in the months must be mapped or ignored in `facts.py`. Credited absences on non-holiday weekdays need their daily credit rows, and a credit row without a matching absence fails the inspection.
7. **Demand.** Save each station month on the Mindestbesetzung page.
8. **Verify.** Open Mitarbeiter for the unit and month: a complete inspection, or the first source error to resolve.

A unit fails loudly rather than partially: one unmapped profession, missing target or orphan credit rejects the whole selection.
