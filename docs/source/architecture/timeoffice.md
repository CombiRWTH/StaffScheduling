# TimeOffice adapter

This reference describes the adapter and the prepared test database. Executed live checks are listed under [current limitations](../validation/index.md).

`api/app/timeoffice/` owns the Microsoft SQL Server integration. It reads TimeOffice into canonical models, writes the project tables and publishes schedules into target plans. The solver depends only on the [domain model](domain.md).

## Modules

| Path under `api/app/timeoffice/` | Responsibility                                                                      |
| -------------------------------- | ----------------------------------------------------------------------------------- |
| `database.py`                    | SQLAlchemy engine using `mssql+pyodbc`                                              |
| `facts.py`                       | Configured units, reference shifts, account IDs, code mappings and planning status  |
| `queries.py`                     | One function per TimeOffice SELECT, returning canonical models                      |
| `project_tables.py`              | Reads and key-scoped writes of the project tables                                   |
| `roster.py`                      | Publication's duty rows, read-back, replacement and clear                           |
| `service.py`                     | `TimeOfficeService`, the package's only public entry point; one connection per call |

## Connection and schema

Follow [database configuration](../getting-started/installation.md#database-configuration) for `.env` and the password file. Docker includes ODBC Driver 18. `database.py` sets `Encrypt=yes` and verifies the server certificate (`TrustServerCertificate=no`) unless `DB_TRUST_SERVER_CERTIFICATE=true`.

The connection boundary checks configuration and driver, bounds login and query waits and sanitizes driver failures. FastAPI returns them as `503` with `integration`, `stage` and an actionable `detail`, never with connection strings, SQL or raw driver errors. Liveness stays independent.

`just connectivity` checks configuration, ODBC, DNS, encrypted login and `SELECT 1` in the API container, bypassing application queries. Offline tests cover missing configuration and driver, sanitized login and query failures and a simulated success. The test server's certificate is self-signed, so it needs `DB_TRUST_SERVER_CERTIFICATE=true`. See [testing](../development/testing.md) and [current limitations](../validation/index.md#webapp-integration).

The adapter reads `TPlanungseinheiten`, `TPlanungseinheitenPersonal`, `TPersonal`, `TPlan`, `TDienste`, `TDiensteSollzeiten`, `TPlanPersonalKommtGeht` and the monthly and daily account tables. `queries.py` holds the SQL.

## Read and write boundaries

`TimeOfficeService` is the whole interface: `get_planning_options`, `inspect_employees`, `list_employees`, `get_employee_calendar`, `set_availability`, `set_wish` (an entry replaces, `None` removes), `get_demand`, `save_demand`, `preview_demand`, `read_generation_input`, `publish` and `clear`. All take and return canonical models. `app.timeoffice` exports only the service, the unavailable error and the engine factory.

Each query function translates its own codes and rejects source faults such as missing master rows, duplicate target plans or unmapped codes. Cross-entity completeness belongs to `domain/inspection.py`. Each router declares the protocol it needs (`PlanningSource`, `AvailabilitySource`, `DemandSource`, `PublicationTarget`). Another planning database can thus replace TimeOffice without touching routes or domain. The mappings in `facts.py` must be checked against the chosen data.

`read_generation_input` builds the solver's `SchedulingDataset` from the inspection, reference shifts, saved demand and trusted context. A reference shift's `TDiensteSollzeiten` rows are its work segments; an overnight segment ends the next day. Each segment's `Minuten` equals its length, so gaps between segments are unpaid breaks:

| Shift | Time        | Breaks (min) | Paid (min) |
| ----- | ----------- | ------------ | ---------- |
| F     | 05:55–13:25 | 30           | 420        |
| Z     | 08:30–14:15 | none         | 345        |
| S     | 13:15–21:00 | 30           | 435        |
| N     | 20:10–06:10 | 15 + 30      | 555        |

Trusted context comes from status-30 plans (`TRUSTED_CONTEXT_STATUS_ID`) of the configured stations. `read_context_coverage` considers the dates the rules reach (`RulePolicy`), at most 5 days before and 3 after the month. Context covers the gap-free run of those dates, next to the month, that such a plan of every station spans. `read_context_duties` groups their worked rows per employee and date. Each group must reproduce a reference shift's segments, and none may fall inside the month; otherwise the read fails. Absences and project availability of the first date after the month complete the context.

All other roster rows are read only as approved absences. Published output, even in a status-20 target, therefore never becomes input or context.

## Monthly accounts and credits

Selection and employee inspection are read-only. They need neither `TPlanPersonal` nor existing duties in a target. Target plans are selected by configured status, interval and exact month bounds. Memberships across the configured units determine jumper pool and home context; jumper pool origin alone never grants eligibility. Missing names, identities, unique targets or accounts fail inspection, as do unknown shifts and ambiguous home origin.

`read_accounts` returns each employee's complete `MonthlyWorkAccount`:

| Value          | Source                                                              | Rule                                         |
| -------------- | ------------------------------------------------------------------- | -------------------------------------------- |
| Target minutes | `TPersonalKontenJeMonat`, account 1 (`SOLL_MONAT`), `Wert2` hours   | Required; explicit zero is kept              |
| Actual minutes | `TPersonalKontenJeMonat`, account 55 (`TOTAL`), `Wert2` hours       | Optional; never treated as a credit          |
| Dated credits  | `TPersonalKontenJeTag` absence-hour accounts, `Wert` hours per date | Each row must fall on an absence of its code |

The credit accounts are 85 `U_STD` (vacation, code `U`), 93 `FI_STD` (internal training, `FI`), 95 `FE_STD` (external training, `FE`) and 97 `ST_STD` (school, `SC`). `docs/adr/0008-credits-from-timeoffice-daily-absence-accounts.md` records why.

TimeOffice books a credit on every Monday-to-Friday absence date that is not an NRW public holiday. The monthly account of the same number is their sum. Inspection fails for a credit without a roster absence of its code (per `read_absences`) and for a credited weekday absence without its credit. A unit working fewer than five days a week would fail this check rather than be credited wrongly. Each credit becomes an `approved_absence` `WorkCredit` with source `TimeOffice <code> absence`.

## Project tables

An authorized preparer runs `api/sql/supplemental-tables.sql` once in the declared database; this needs DDL permission. The API never creates tables. The runtime login needs SELECT, INSERT and DELETE on all four. Without them, inspection, configuration and generation fail with a query-stage `503`. The test database has them; its single login holds `db_ddladmin`, `db_datareader` and `db_datawriter`, so setup and runtime privileges are not separated there.

| Table                             | Key                                 | Meaning                                                                    |
| --------------------------------- | ----------------------------------- | -------------------------------------------------------------------------- |
| `dbo.StaffSchedulingAvailability` | employee, date                      | Canonical availability type, JSON `shift_ids` for `available_only`, reason |
| `dbo.StaffSchedulingWish`         | employee, date                      | Canonical wish type and optional shift                                     |
| `dbo.StaffSchedulingDemandMonth`  | station, first of month             | The station month's demand has been saved                                  |
| `dbo.StaffSchedulingDemand`       | station, date, shift, qualification | Required count ≥ 1; a missing row in a saved month requires nobody         |

The Mitarbeiter page needs the tables too, since inspection reads `StaffSchedulingAvailability`. Every write runs in one transaction and first validates that the employee has a membership in a configured unit that month, that shifts are reference shifts and that a demand station has a target plan. An availability or wish save replaces exactly one employee date. A demand save replaces exactly one station month and marks it saved. Writes need no plan or roster rows, so they work on empty targets. Serialize them like every shared database change.

`docs/adr/0006-monthly-configuration-in-project-tables.md` records why these tables replace native `Wunschdienst` rows and the old `StaffSchedulingMinimalStaffing` table; the API reads neither. Generation reads the month's wishes of every inspected employee, jumper pool members included. The four reference shifts are facts in `facts.py`: F `1113`, Z `1453`, S `1605`, N `1690`. Their codes come from `TDienste`, their types from the facts. Staff levels and availability types are stored as canonical values.

## Publication

`publish` writes the accepted schedule under review into the selected stations' target plans for the month; `clear` removes it. `docs/adr/0009-publish-marked-duties-into-timeoffice-target-plans.md` records the decision. The route takes the assignments from `Review.publishable` (`api/app/solver/review.py`); the adapter never receives plan IDs.

!!! warning "Writes to TimeOffice"

    A target plan's published output is its worked rows marked `Info` = `StaffScheduling` (`GENERATED_DUTY_INFO`). Worked rows carry no absence code in `RefgAbw`/`RefDienstAbw` and are not `Wunschdienst`. Publication deletes and replaces exactly these `TPlanPersonalKommtGeht` rows of the named stations' target plans. Absences, native wishes, duties entered in TimeOffice, other plans and other months are kept. The runtime login needs SELECT, INSERT and DELETE on that table; the test login's `db_datawriter` role covers this.

In one transaction, before deleting anything, `publish`:

1. selects each station's single target plan by the rule all reads share (`read_target_plans`); none is `422`, several are `409`,
2. checks that every duty lies in a named station and the month, uses a reference shift and is the employee's only duty that date,
3. finds the profession (`RefBerufe`) of the employee's active station membership whose mapped qualification equals the duty's credited qualification, and fails unless exactly one exists,
4. refuses (`conflict`, naming employee and date) a duty on a date with an absence or a kept worked row, such as a duty entered in TimeOffice or in another plan,
5. counts and deletes the old output, inserts the new rows and rolls back (`read_back`) unless they read back as the schedule.

Only then does it commit; any failure also rolls back the deletion. Publication and clear hold a process lock and run `SERIALIZABLE`, so a concurrent writer from another process fails instead of interleaving. A deadlock (SQL Server error 1205 or SQLSTATE `40001`) or duplicate key (2627, 2601, read from the driver message) becomes `TimeOfficeConflict`, returned as `409` `concurrent`. Other driver failures, including foreign-key or NOT NULL violations, stay sanitized `503`s. A failed commit returns `503` with stage `commit`: the outcome is unknown. Run one API process. All multi-row inserts use pyodbc's `fast_executemany`; a month publishes in about a second.

A duty becomes one `TPlanPersonalKommtGeht` row per segment of its reference shift, as TimeOffice stores worked duties:

| Column                                     | Value                                                             |
| ------------------------------------------ | ----------------------------------------------------------------- |
| `Datum`                                    | The duty's start date, also for a night's last segment            |
| `VonZeit`, `BisZeit`, `Minuten`            | The segment's wall-clock times and paid minutes                   |
| `RefStati`                                 | Row status 20                                                     |
| `RefBerufe`                                | The profession from step 3                                        |
| `RefPlanungseinheiten`, `RefPeinheitOwner` | The station, also for a jumper pool employee                      |
| `Info`                                     | `StaffScheduling`                                                 |
| `lfdNr`                                    | After the employee's kept rows of that status and date, else 1..n |

On a clock-change night, elapsed time differs from paid `Minuten` by an hour. The roster key `(RefPersonal, Datum, RefStati, lfdNr)` excludes the plan, hence the numbering; a native wish keeps its number.

Deployment type, readiness times and other source detail are not written. Read-back accepts only rows reproducing a reference shift. Planners must not put the marker into `Info` of their own duties. No `TPlanPersonal` rows are created, and the prepared plans have none; whether the TimeOffice client lists published employees without them is unverified.

## Prepared units

`facts.py` configures three existing units of the test database for January–June 2026:

| Unit (`KurzBez`) | `Prim` | Role                                                                  |
| ---------------- | ------ | --------------------------------------------------------------------- |
| `PE 77`          | 77     | Station                                                               |
| `PE 79`          | 79     | Station                                                               |
| `PE 408`         | 408    | Jumper pool for both stations (no demand group, its staff homed here) |

Employees, contracts, home memberships and monthly target plans are native. The SQL files in `api/tests/timeoffice_preparation/`, applied in name order, prepare every other input the [checklist](#supporting-another-unit) needs:

| File                               | Prepares                                                                                                                                                          |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `01-replacement-memberships.sql`   | Replacement memberships of the 7 jumper pool employees at both stations, 2025-12-01 to 2026-07-31                                                                 |
| `02-exclude-rotating-trainees.sql` | `KeinEPlan` on 15 station memberships of rotating trainees (home in a school unit, members for part of a month)                                                   |
| `03-monthly-targets.sql`           | 151 missing account-1 targets, derived like the native ones: NRW working days × weekly hours ÷ 5                                                                  |
| `04-vacations-and-credits.sql`     | One Monday–Friday vacation week (`U`) per professional and per assistant and MFA of 77, with its daily vacation credit; jumper pool absences sit in its June plan |
| `05-context-plans.sql`             | Empty trusted context plans (status 30, day interval 4) for 2025-12-18..31 and 2026-07-01..07, so the context is known to be free                                 |
| `06-demand.sql`                    | Dated demand of all twelve station months (see [examples](../validation/examples.md#input-data-and-boundary-context))                                             |
| `07-availability-and-wishes.sql`   | 7 project availability rows and 32 demonstration wishes                                                                                                           |
| `readiness.sql`                    | Read-only checklist per unit and month; every row carries `ok`                                                                                                    |

Each file ends with a read-back of its rows and converges, so a second run changes nothing. All insert missing rows. `02` sets `KeinEPlan` where it differs. Demand, availability and wishes also update differing rows and delete other rows in their scope. Native targets are never changed, so `03`'s read-back only checks that each employee-month has a valid target. No file writes `TPersonal` or another unit's rows.

`just test-timeoffice` runs every file in one transaction and rolls back. It fails unless every `ok` is 1 and no write changes a row. `TIMEOFFICE_PREPARATION=apply` commits each file instead (see [live verification](../development/testing.md#live-timeoffice-verification)).

Native facts the preparation relies on:

- Each station month has one target plan (status 20, interval 1, exact month bounds). The adapter neither creates nor changes plans.
- The jumper pool has its own plan of that form but is never selectable.
- Month-shaped context plans would collide with native plans on the unique index `TPlan(RefPlanungseinheiten, VonDat, RefPlanungsIntervalle)`, so the prepared ones use the day interval. A context plan is complete for every date it spans.
- An absence row sets `RefgAbw` and `RefDienstAbw` to the absence code and `Minuten` to 0. The roster key allows one row set per employee, date and row status across all plans, absences included.
- Generation must select both stations together. The jumper pool's monthly balance is hard, so a one-station run would give the jumper pool its whole target there. Publishing the second station would then conflict.

## Supporting another unit

Check each item with read-only queries, then add the unit to `planning_unit_type_by_id` in `facts.py`:

1. **Unit.** Monthly interval (`RefPlanungsIntervalle` 1); decide whether it is a station or a jumper pool.
2. **Target plans.** Exactly one plan per planned month with status 20, interval 1 and exact month bounds. Generation ignores worked rows already in it; [publication](#publication) replaces them.
3. **Memberships.** Every `TPlanungseinheitenPersonal` row overlapping a planned month (`KeinEPlan` 0) needs a profession mapped in `STAFF_LEVEL_BY_PROFESSION_CODE`. Each employee needs exactly one home unit (`IstHeimat`) on every active date. Jumper pool staff need replacement memberships at the stations they may cover.
4. **Employees.** A name and a mapped profession in `TPersonal`.
5. **Accounts.** A target (account 1) for every employee and planned month.
6. **Absences and credits.** Every absence code in the months must be mapped or ignored in `facts.py`. Credited weekday absences need their daily credit rows.
7. **Demand.** Save each station month on the Mindestbesetzung page.
8. **Verify.** Open Mitarbeiter for the unit and month: a complete inspection, or the first source error to resolve.

One unmapped profession, missing target or orphan credit rejects the whole selection.

## Limitations

- **No wish or availability synchronization.** TimeOffice has no equivalent that keeps their meaning, so `Wunschdienst` rows are not imported and app entries stay invisible in TimeOffice.
- **Context duties must match a reference shift exactly.** Variant shifts sharing a code (another `F` or `S` row of `TDienste`) stop generation instead of being guessed.
- **Duties outside the configured stations are not seen.** Generation ignores in-month duties in other units or plans; publication then refuses the conflict. Employee 791 has native duties in the June target plan of `PE 77` on 2026-06-08..12; project availability blocks those dates. Rest against another unit's duty at the month edge is not checked.
- **No Sunday history is read.** The annual minimum of employment-free Sundays is not assessed.
- **Some mappings are assumptions.** In `facts.py`, profession `-` as trainee, Servicekraft as professional, Praktikant as assistant and the absence codes `AZV`, `K`, `TB` and `SO` as unavailable are unverified and marked there.
