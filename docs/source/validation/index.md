# Evidence and current limitations

This checkout provides a reproducible development foundation with checked monthly generation, review, validated import, portable downloads and scoped publication to TimeOffice. The final example dataset remains unfinished. These limits describe current code and executed checks; they are not promises inferred from visible controls.

## What this section proves

For evaluators and anyone deciding whether to rely on a result. The checks below cover the current foundation and generation; a live January schedule of the original stations was accepted by the independent check, earlier example units were published and cleared on the test database, but no exported example bundle is claimed yet. [Reasoning and requirements](reasoning.md) explains policy choices and evaluation; [examples and reproduction](examples.md) will document the accepted deliverables.

## Startup and connectivity

Image-built development Compose startup, actual Next-server/API HTTP connectivity, bounded unavailable-database/API states, persistent output recreation and separate source reload passed in Linux arm64 containers on macOS. A Linux amd64 API build/import check includes ODBC Driver 18. `/status` reports API liveness; Next `/api/health` checks API process connectivity. Neither claims database readiness. The configured test server presents a self-signed certificate; with the explicit `DB_TRUST_SERVER_CERTIFICATE` opt-in the read-only diagnostic passes all stages and live read-only planning options and shift times load. Connected browser flows, hosted CI and actual Linux-host acceptance remain outstanding. The Compose file runs development servers; a production build/deployment is a separate gate. The root just recipes, including `just run`, need a POSIX shell: on Windows they are meant for Git Bash or WSL, not the Command Prompt or PowerShell, and Windows use is untested.

## Webapp integration

The webapp is a plain Next.js App Router project. The home page, canonical month/station selection with complete read-only employee inspection, and monthly configuration (availability, wishes and dated staffing demand with a weekly pattern) are implemented, with controlled browser evidence. Generation of the full month with transient job states and the review of its schedule, with import and download of portable files and its explicit publication and clear, are implemented. Recurring settings and templates are not part of the application; optimization controls are omitted. Generation considers wishes as one objective tier; they never bind. On the test database the project tables and the [prepared inputs](examples.md#input-data-and-boundary-context) of stations `PE 77` and `PE 79` and jumper pool `PE 408` exist. Live checks on 2026-10-02 at revision `c6eb998`, through the running Compose instance against the test database:

| Check (command)                                                   | Expected                                         | Actual                                                   |
| ----------------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------- |
| `GET /planning/options?year=2026&month=1`                         | The two stations                                 | `PE 77`, `PE 79`                                         |
| `GET /employees` for both stations, each month January–June       | Complete inspection, jumper pool associated      | 53 employees, jumper pool 408, every month               |
| Webapp **Mitarbeiter** for both stations, each month January–June | Complete table, no error                         | 53 rows each month, 0.3–3 s per page                     |
| `just test-timeoffice`                                            | Preparation converged, every readiness check met | Both tests pass; no write changes a row; every `ok` is 1 |

Earlier checks on prepared example units, since removed, also covered saving twelve station months of demand through `POST /demand/pattern` and `PUT /demand` (read back unchanged), availability and wish round trips (`PUT`, read back, `DELETE`) and the rejection of an employee outside the configured units (`422`). Removing those units deleted only their own rows: the count and checksum of every other row of the affected tables stayed unchanged.

## Solver and schedule check

`POST /generation` runs the solver for one full month in a background job; `GET /generation` reports the latest job, and every found schedule carries the independent [schedule check](../architecture/solver.md#result). The solver implements every agreed hard rule, including trusted context around the month, relaxes only staffing through reported gaps, and optimizes its six tiers as lexicographic stages; inputs include the project wishes and exclude in-month roster work.

The examples carry 32 demonstration wishes in the project table: two per station and month and one of a jumper pool employee per month, covering all four wish types; two are deliberately not grantable (a late shift on an early-only day, and a wish inside the employee's own vacation). Solves of every month through the adapter's own reads and the production solver, both stations together, 300 s, on the current solver code with the stations configured as now (2026-10-02):

| Month | Solver status | Duties | Jumper pool duties | Gap slots                  | Findings | Wishes (granted, denied, not grantable) |
| ----- | ------------- | ------ | ------------------ | -------------------------- | -------- | --------------------------------------- |
| Jan   | `feasible`    | 1080   | 161                | 0                          | 0        | 5, 0, 0                                 |
| Feb   | `feasible`    | 1014   | 154                | 5 (MFA, its vacation week) | 0        | 5, 0, 0                                 |
| Mar   | `feasible`    | 1146   | 173                | 0                          | 0        | 5, 0, 2                                 |
| Apr   | `feasible`    | 1051   | 152                | 0                          | 0        | 5, 0, 0                                 |
| May   | `feasible`    | 941    | 144                | 0                          | 0        | 5, 0, 0                                 |
| Jun   | `feasible`    | 1070   | 134                | 0                          | 0        | 5, 0, 0                                 |

January's check is `accepted`. February to June are `incomplete` only because their first days have no trusted context yet; the month-by-month sequence supplies the preceding accepted month. A January run through the webapp at 60 s was also `accepted` with 0 findings, but stopped with 269 gap slots in the top stage (bound 0): 60 seconds are too short for these stations, so the example months use 300 seconds.

On the earlier example units, January runs compared the objectives (both stations, 2026-10-02):

| Run                             | Solver status | Duties | Check      | Stages (gaps, health, station transfers, wish cost, balance minutes, surplus intermediate) | Wishes (granted, denied, not grantable) |
| ------------------------------- | ------------- | ------ | ---------- | ------------------------------------------------------------------------------------------ | --------------------------------------- |
| Weighted objective, 120 s       | `feasible`    | 1055   | `accepted` | –, 65, –, –, 2529, 182 (no gap, transfer or wish tier)                                     | not considered                          |
| Staged without transfers, 120 s | `feasible`    | 1050   | `accepted` | 0 optimal, 40, –, 0 optimal, 618, 173                                                      | 2, 0, 0 (before the example wishes)     |
| Staged without transfers, 300 s | `feasible`    | 1056   | `accepted` | 0 optimal, 21, –, 0 optimal, 498, 195                                                      | 8, 0, 1                                 |
| Staged, all six tiers, 300 s    | `feasible`    | 1055   | `accepted` | 0 optimal, 38, 0 optimal, 0 optimal, 258, 185                                              | 8, 0, 1                                 |

Every stage value equals the score the check recomputes, and each 300-second bundle re-reads as a valid import with all five files identical to their rendering. The open items are the after-month boundary (checked by the next run) and annual free Sundays. Each stage gets only part of the time limit, so the top tier needs a longer total limit than the weighted objective did: at 120 seconds the staged runs had 40–84 health events, at 300 seconds 15–38; results vary between runs because the search is parallel and time-limited. The example months therefore use 300 seconds. Proven bounds stay weak (health bound 0), so the stages are `feasible`, not `optimal`.

On the earlier example units, a weighted June run (120 s, 1096 duties, 0 findings) stayed `incomplete` for lack of May context, which the six-month sequence supplies. The first June run was infeasible: the prepared July context left no professional able to work the June 30 night (a fourth night in a row, or a duty inside the 48-hour recovery). The solver's diagnostic named this shortage, and the context was corrected by removing three trusted July 3 night duties; no rule was relaxed.

Jobs are lost on API restart. Monthly runs are independent; the coordinated six-month example files are pending. The application writes key-scoped saves to the project tables (availability, wishes, demand) and, only through explicit publication and clear, the worked rows of the stations' target plans.

## Review, import and export

**Prüfen** reviews the latest generated or imported schedule; `ScheduleBundle` validates imports and renders the five portable files, and the example tests validate and re-solve bundle folders without TimeOffice ([examples and reproduction](examples.md#bundle-files)). Live check on 2026-10-02 through the running Compose instance against the earlier prepared example units:

| Check                                                                       | Expected                                    | Actual                                                                     |
| --------------------------------------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------- |
| `POST /generation`, January 2026, both example stations, 120 s              | A found schedule, reviewed automatically    | `feasible`, check `accepted`, 1059 duties, 0 findings                      |
| Webapp `/review` for January and both stations                              | Review page with summary, grid and accounts | `200`; 57 employees, staffing of both stations                             |
| Webapp `/review/files/{name}`, all four files (before `gaps.csv`)           | Attachments of the reviewed bundle          | `200`; 233 kB input, 183 kB result, 160 kB schedule, 69 kB employee tables |
| Example validator (`check_examples`) on the downloaded folder, January only | Accepted single month of both stations      | No problem; open: following month's start, annual free Sundays             |

The pair passed the same validation as an import. A single month cannot show the sequence checks; they are covered by the offline tests until the six accepted months exist. Messages of findings and the API's import details are English; the webapp names import problems in German. The review is lost on API restart and is not a saved library.

The pages at revision `22d1c6c` were checked read-only against the same example units through the running Compose webapp (page loads only; no write was triggered):

| Check                                         | Expected                                          | Actual                                                                                                               |
| --------------------------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| All six pages for January 2026, both stations | `200`, no webapp or API errors                    | `200` each; logs clean                                                                                               |
| **Mitarbeiter**, details of one employee      | Accounts in hours, no raw IDs or provenance       | 57 employees; _Soll 163:48 h_, credits _7:48 h · Genehmigte Abwesenheit_                                             |
| **Erstellen** with the latest January job     | Headline, fact row and review link                | _Dienstplan erstellt, Regeln eingehalten_, 1072 duties, **Dienstplan prüfen**                                        |
| **Prüfen** summary and grid                   | Status line, actions; transfers marked with codes | _Regeln eingehalten · Kann veröffentlicht werden_; 143 transfers, short station codes on one line; no truncated name |

Live publication and clear through the confirmation panels of that revision were not repeated; their backend behaviour is unchanged and the panels are covered by the offline browser flows.

## Publication and clear

Publication writes the accepted schedule under review into the stations' target plans and clear removes it ([procedure](../user-guide/publication.md), [storage](../architecture/timeoffice.md#publication)). Live check on 2026-10-02 against the earlier prepared example units, one writer, through the running Compose API and webapp. Before and after every step the target plans' rows were counted by kind, and all roster rows outside the example plans and the example plans' absence and context rows were checksummed:

| Step                                                                    | Expected                                              | Actual                                                                                          |
| ----------------------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Generate January, both example stations, 120 s                          | Accepted schedule under review                        | `feasible`, `accepted`, 1059 duties, 0 findings                                                 |
| `POST /publication`                                                     | 1059 duties written and read back, nothing removed    | `200`; 1995 rows (one per segment), nights dated on their start, jumper duties in station plans |
| Read-only SQL after publishing                                          | No duty on an absence date; everything else unchanged | 0 such duties; 32307 other roster rows and 2272 example absence/context rows, checksums equal   |
| Generate January again                                                  | Published rows are not input                          | 0 in-month context duties; `accepted`, 1051 duties                                              |
| `POST /publication` with the first schedule's `received_at`             | Refused, no change                                    | `409` `changed`                                                                                 |
| `POST /publication` of the new schedule                                 | Replacement                                           | 1059 removed, 1051 published                                                                    |
| Webapp **Prüfen**, second station only: clear cancelled, then confirmed | Only that station's duties removed                    | _Entfernt: 606 veröffentlichte Dienste_; the first station's rows and all checksums unchanged   |
| Webapp **Prüfen**, both stations: publication cancelled, then confirmed | Committed and read back                               | _Veröffentlicht: 1051 Dienste geschrieben und gelesen, 445 bisherige ersetzt_                   |
| `DELETE /publication`, both stations                                    | Targets empty again                                   | 1051 removed; every count and checksum equals the starting state                                |

Each publication and clear took about one second. A second live check on the same day, after publication was limited to rows marked `Info` = `StaffScheduling`, prepared three unmarked rows in the first station's January target first (a native wish on an employee's duty date, a weekend absence on another employee's duty date and a duty entered as if by hand) and removed them again at the end:

| Step                                                                                                           | Expected                                                       | Actual                                                                                                                                            |
| -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST /publication` of an accepted January schedule (1056 duties)                                              | Refused for the absence, no change                             | `409` `conflict` naming the employee and date; all counts and checksums equal                                                                     |
| Remove the absence, publish again                                                                              | Published; wish and entered duty kept                          | 1056 duties in 2002 marked rows; the wish keeps `lfdNr` 1 and the duty that date is numbered 2–3; the entered duty unchanged and unmarked         |
| Two separate processes publish the same schedule at once                                                       | One commits, the other fails without a change, or both in turn | One committed (1056 replaced); the other was SQL Server's deadlock victim and returned `TimeOfficeConflict`; 1056 duties, no duplicate roster key |
| `DELETE /publication`, both stations                                                                           | Only marked duties removed                                     | 1056 removed; wish and entered duty kept                                                                                                          |
| Availability and wish `PUT`/`GET`/`DELETE` for one employee; demand of one station month saved again unchanged | Read back, removed; demand identical                           | Read back, both `204`, empty afterwards; 280 demand cells identical                                                                               |

After removing the prepared rows every count and checksum equalled the starting state. Insert-failure rollback and ambiguous targets were not provoked live; the offline adapter tests own them. Whether the TimeOffice client displays published duties without `TPlanPersonal` rows was not checked.

## Further development

- **Ersatz example data.** Station transfers through a replacement membership (Ersatz) are modelled and minimized below health and above wishes, but the example data gives replacement memberships only to the jumper pool, so the examples show no station transfer.
- **Wish variants.** Maximizing the number of granted wishes first and only then their fairness, or minimizing the largest number of denials of any employee, are alternatives to the adopted cubic fairness cost.
- **Native wishes.** TimeOffice's own wish rows (`Wunschdienst`) are not read; wishes come from the project table only.

## Quality gates

The latest executed offline suite reports **140 passed** and one skipped (the committed examples, which do not exist yet), including the solver integration tests; no test is excluded to manufacture success. The removed solver plugin tests are replaced by the schedule-check boundary examples (`test_schedule_check.py`) and production solves (`test_solver.py`).

Webapp strict TypeScript and the native production build pass. The twenty-four controlled browser scenarios (selection/inspection, unavailable/incomplete reads, back navigation, the overview's planning cards in order, the sidebar of implemented areas, year entry and the January default, mobile navigation, availability edit/reload/delete with wishes, failed availability save, demand save/reload/reset/pattern with per-cell change marks, invalid count, failed demand save, generation without result or with incomplete input, a running generation across navigation with busy rejection and its accepted schedule check, infeasible versus failed runs, review of a generated schedule with its status, collapsed technical details, jumper-pool transfer markers and downloads, import of a matching pair and rejection of a mismatched pair without losing the review, imported home changes and unknown origins in the grid, a schedule of another scope, publication and clear each cancelled and then confirmed, a publication refused after the schedule under review changed, a failed publication that changes nothing, and no publication of an incompletely checked schedule) pass through the real pages/API with fictional SQL results; these do not establish live TimeOffice or Microsoft SQL Server execution evidence.

Formatting, API Ruff/Pyright, all configured Git hooks and strict documentation builds pass. Webapp ESLint reports no findings. React Doctor passes with two visible warnings asking for pnpm's `minimumReleaseAge` and `trustPolicy: no-downgrade`. Neither setting is enabled, because the current lock does not satisfy them: `pnpm install --frozen-lockfile` would reject the locked releases younger than seven days and two transitive entries (`semver` 6.3.1, `eslint-import-resolver-typescript` 3.10.1) whose trust evidence is weaker than that of earlier versions. Enabling them needs a refreshed lock. `just check` runs all independent offline gates, including browser flows, production build and docs, and retains a failing exit status.

## Retired material

The old API CLI, separate frontend Python launcher, archived backend and service case directories were removed. Their setup instructions, JSON-file recipes, VM installer, screenshots, duplicated guides and historical documentation are no longer published here. Git history preserves older versions. Current contracts live in the source and these references; no alternative legacy setup is supported.
