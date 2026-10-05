# Testing

Run commands from the repository root after the [native tool installation](../getting-started/installation.md#optional-native-developer-setup). `just run` and the CI image job need Docker. [Current limitations](../validation/index.md) records failing gates and open evidence.

## Unit responsibilities

`just test` runs the offline API suite, including tests marked `integration`. Two markers are excluded by default:

| Marker         | Tests                                                  | Run with                    |
| -------------- | ------------------------------------------------------ | --------------------------- |
| `timeoffice`   | Need the authorized external test database             | `just test-timeoffice`      |
| `reproduction` | Solve the committed example inputs again; take minutes | `just test -m reproduction` |

`test_schedule_check.py` owns every hard rule and objective score through `check_schedule`. It tests each rule at its discriminating boundary:

- Qualification: credited versus employee qualification, MFA demand, a jumper pool employee at two stations.
- Availability: touched and following-date entries, narrowing allowed-shift restrictions.
- Time: the ±460-minute band, exactly 11 hours of rest, three versus four nights across the month start, exactly 48 hours of recovery, daylight-saving times.
- Work: break and daily-work limits (against the solver's own diagnostics), the monthly average, replacement rest days, a Saturday night as Sunday work.
- Input: context counted once, malformed assignments, a shortfall accepted only as its declared gap.
- Wishes: every type at its granted/denied boundary, four not-grantable causes, the cubic cost per employee and group.
- Health: station transfers for station members only, isolated workdays at both month edges, back-to-back weekends with a Friday night and preceding context.

`test_solver.py` owns production solves through `SolverService` (integration). Every solve asserts that each stage value equals its checked score. It also checks that every objective tier is a score field. The cases cover:

- An accepted month with every stage optimal.
- Time limits: each stage but the last gets half of the remaining time. A later stage without time keeps the previous schedule as feasible.
- Context ruling out a fourth night, and the October clock-change night that breaks the break rule.
- Unmet demand returned as exactly its gaps. An intermediate gap never offsets a surplus elsewhere.
- A non-staffing conflict stays infeasible. A month is refused without every account and solved with them.
- A jumper pool employee needed at two stations gets one duty and one gap.
- Fairness spreads two unavoidable denials 1 + 1 against the balance. An ungrantable wish costs nothing.

The objective order is tested at one-step boundaries:

| Higher priority                                            | Outweighs                   |
| ---------------------------------------------------------- | --------------------------- |
| Gaps                                                       | Health                      |
| Health                                                     | A station transfer, balance |
| A station transfer                                         | A wish                      |
| Health, one isolated workday or back-to-back weekend fewer | A wish                      |
| Wishes                                                     | Balance                     |
| Balance                                                    | Extra intermediate duties   |

`scheduling.py` builds the small canonical inputs for both files. A new hard rule or objective adds its examples to both files; see [changing the solver](../architecture/solver.md#adding-or-changing-a-hard-rule).

| File                            | Owns                                                                                                                                    |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `test_settings.py`              | Secret loading                                                                                                                          |
| `test_inspection_rules.py`      | Adding only the jumper pools that station members call home                                                                             |
| `test_monthly_configuration.py` | The NRW calendar and weekly-pattern expansion                                                                                           |
| `test_generation.py`            | The generation job: immediate acceptance, busy rejection, lock release after failures, sanitized errors                                 |
| `test_foundation.py`            | Liveness without credentials, database error sanitization and TLS, driver/settings validation, diagnostic cleanup and read-only queries |

## Service and adapter integration

Compose healthchecks gate `docker compose up --wait` on API liveness and on the Next `/api/health` handler. That handler makes a real request to the API. The CI image job validates the Compose file, builds both images without credentials and checks the API image's ODBC driver.

Editing a live bind mount reloads FastAPI and Next without a rebuild. Host `.venv`, `node_modules`, `.next`, local environment files and secrets stay out of image build contexts. Container dependency and build volumes mask the host directories.

### Adapter fixture

`api/tests/inspection_fixture.py` substitutes SQL query results. Production queries, inspection validation and HTTP routes stay in use; production never imports the fixture. It supplies:

- Fictional employees, stations and complete monthly declarations.
- Trusted context plans for the last 14 days of every month, with one trusted night on December 31.
- Deliberate failure months and failing write IDs.
- In-memory project tables and roster that apply the adapter's parameters and roll back failed transactions.

The fixture recognizes the adapter's statements by their text. It tests the adapter's decisions, not the SQL. SQL Server behaviour is covered by the [live checks](../validation/index.md#publication-and-clear).

### API service tests

| File                            | Owns                                                                                                                                                              |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `test_employee_inspection.py`   | Source completeness, identity, memberships, jumper pool eligibility, accounts, TimeOffice code translation, HTTP validation                                       |
| `test_monthly_configuration.py` | Scoped availability, wish and demand writes; native absences survive; validation before writing; pattern preview; HTTP `422`                                      |
| `test_generation.py`            | Generation input from `TimeOfficeService.read_generation_input`, and the generation HTTP contract                                                                 |
| `test_review.py`                | Schedule tables, bundle files and round trip, every import rejection, `besetzung.csv` and `gaps.csv`, published schemas, the review/download/import HTTP contract |
| `test_examples.py`              | The example validator and the committed months in `plaene/`                                                                                                       |
| `test_publication.py`           | Publication and clear through `TimeOfficeService` and over HTTP                                                                                                   |

Generation input ignores polluted roster rows and keeps approved absences. The fixture applies the roster query's own absence filter, so a query that read worked shifts would fail. Worked duties come only from trusted context plans; a context duty that differs from its shift fails. Only the selected station and its jumper pool are units, and only the month's project wishes are input. A station without saved staffing is refused. Shift segments, breaks and paid minutes come from the target-time segments. Over HTTP, one real solve reaches `completed` with an `accepted` check. The test also checks `404` before any job and after a restart, `422`/`409` without a job and `423` while busy.

A stale published schema is rewritten and fails the review test once.

The example validator accepts a consistent two-month sequence of both stations. It rejects changed files, context that differs from the neighbouring month, a rejected month, missing or extra stations and misplaced folders. The `reproduction` tests in `test_examples.py` solve every committed input again. The example generation is a `timeoffice` test that runs only with `PLAENE_GENERATION=write`; see [examples and reproduction](../validation/examples.md).

Publication writes one row per segment into the destination station's target plan, with the membership profession and the `Info` marker. A jumper pool night goes into the other station's plan, dated on its start. Numbering continues after a kept native wish. Absences, wishes, duties entered in TimeOffice and other-plan duties are kept. A second write waits for the first. Invalid schedules are rejected before any deletion. A failed insert, collision or differing read-back (`read_back`) rolls the deletion back; a failed commit reports stage `commit`. Over HTTP it publishes only with the reviewed `received_at` and stations. It maps `conflict`, `concurrent`, `503`, `not_accepted` and `changed`; an empty schedule raises `InvalidSelection` (`422`). `test_foundation.py` checks that deadlocks and duplicate keys become a sanitized `TimeOfficeConflict`. A foreign-key violation stays a query failure.

## Staff-admin browser flows

Selection and inspection, monthly configuration, generation, review with import/export, and publication/clear are automated.

```sh
just install
just test-browser
```

- The locked `@playwright/test` runner uses Chromium, installed by `just install`.
- Linux hosts also need `pnpm --dir webapp exec playwright install --with-deps chromium`.
- Tests need the native tools and free loopback ports 18080 and 18081.
- The runner starts its own API and Next servers and refuses to reuse an existing process.
- No other `next dev` may run for `webapp/`; Next.js allows one development server per project directory.
- No database credentials or Docker are needed.
- `just check` runs the flows as an independent gate. CI runs them in a separate job.

Failure traces are kept under the ignored `webapp/test-results/`. Inspect one with `pnpm --dir webapp exec playwright show-trace <path>`.

### Browser API

`api/tests/browser_server.py` overrides the adapter dependency in the test process with the [adapter fixture](#adapter-fixture). Found schedules go to the same in-memory review as in production. Staffing is seeded for Station North in June to August:

| Month  | Generation result                                                                                 |
| ------ | ------------------------------------------------------------------------------------------------- |
| June   | Real solve; one shift stays a gap                                                                 |
| July   | Substituted solver crash, after two seconds                                                       |
| August | Real solve with unreachable accounts (two professionals needed, one available), after two seconds |

Deliberate failures are fixed in the fixture:

- Saves for "Example Jumper Three" (availability) and "Example Station South" (demand) fail.
- Every roster write at Station South fails.
- June at Station South has no trusted context, so its schedule is incompletely checked and offers no publication.

### Flows

All flows live in `webapp/tests/browser/`.

| Spec                    | Covers                                                                                                                                             |
| ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `selection.spec.ts`     | Station/month selection, employee table, hours and credits, filters, empty/incomplete states, URL selection, navigation and mobile navigation      |
| `configuration.spec.ts` | **Verfügbarkeit** entries and wishes, **Mindestbesetzung** demand, weekly pattern, per-cell change marks, invalid counts, deliberate save failures |
| `generation.spec.ts`    | Refused starts, a real June solve, the busy message, completed, infeasible and failed jobs with German messages                                    |
| `review.spec.ts`        | Review summary, gaps, wishes, schedule and accounts, the five downloads, import, and two crafted imports through the real validation               |
| `publication.spec.ts`   | Publication and clear confirmations, a replaced schedule, a failed write that changes nothing, a schedule without trusted context                  |

Some details matter when changing the webapp:

- Accessible text is the selector contract. Change marks use "Geändert, gespeichert: _n_"; transfers use _Einsatz außerhalb der Herkunft_.
- A missing or invalid month redirects to January of the current year.
- The sidebar links the overview plus exactly the five implemented areas.
- The solver's English messages appear only in **Technische Details**.
- The API tests own every import rejection except a changed input with the old result.
- Crafted imports must pass the real validation, whose re-check reproduces the stored check exactly. A home change to the jumper pool on June 16 marks only later duties as transfers.
- An accepted schedule without duties cannot be produced from the fictional data. No browser flow exercises the webapp's message for it.

## Live TimeOffice verification

With services running, `just connectivity` checks configuration, ODBC, DNS, login and `SELECT 1` only. It never runs application queries. It needs the connection settings, password and network prerequisites in [installation](../getting-started/installation.md#database-configuration). The current test server needs `DB_TRUST_SERVER_CERTIFICATE=true` for its self-signed certificate.

`just test-timeoffice` runs only the `timeoffice` tests. They run in the API image with its ODBC driver, `.env` and password secret. The working tree's tests are mounted read-only.

`test_timeoffice_preparation.py` owns the [prepared units](../architecture/timeoffice.md#prepared-units):

- It runs each file of `api/tests/timeoffice_preparation/` in order in one transaction, then rolls back.
- It fails unless every read-back `ok` is 1 and no write changes a row.
- `readiness.sql` must report every check `ok`.
- The configured units, the adapter's mappings and the NRW holidays are passed as temporary tables, so the test checks `facts.py` itself.
- `TIMEOFFICE_PREPARATION=apply` commits each file instead and stops at the first failing one.

Live publication checks run by hand, one writer at a time, on the prepared targets:

1. Record the target plans' rows by kind and checksums of all other roster rows.
2. Publish and clear through the API or the webapp.
3. Compare after every step.
4. Finish with the targets empty again.

[Current limitations](../validation/index.md#publication-and-clear) lists the executed run.

## Linux and clean-checkout checks

The foundation ran in Docker Desktop Linux arm64 containers on macOS, including ODBC Driver 18, HTTP connectivity and reload. A Linux amd64 API image passed build, import and ODBC checks.

To repeat the verification on a Linux host:

1. Frozen-install the native tools.
2. Run `just check` and keep every failing result.
3. Run `just connectivity` separately with authorized configuration.
