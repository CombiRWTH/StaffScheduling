# Evidence and current limitations

This checkout provides a reproducible development foundation with checked monthly generation, review, validated import, portable downloads and scoped publication to TimeOffice. The final example dataset remains unfinished. These limits describe current code and executed checks; they are not promises inferred from visible controls.

## What this section proves

For evaluators and anyone deciding whether to rely on a result. The checks below cover the current foundation and generation; a live January schedule was accepted by the independent check and published and cleared on the prepared test database, but no exported example bundle is claimed yet. [Reasoning and requirements](reasoning.md) explains policy choices and evaluation; [examples and reproduction](examples.md) will document the accepted deliverables.

## Startup and connectivity

Image-built development Compose startup, actual Next-server/API HTTP connectivity, bounded unavailable-database/API states, persistent output recreation and separate source reload passed in Linux arm64 containers on macOS. A Linux amd64 API build/import check includes ODBC Driver 18. `/status` reports API liveness; Next `/api/health` checks API process connectivity. Neither claims database readiness. The configured test server presents a self-signed certificate; with the explicit `DB_TRUST_SERVER_CERTIFICATE` opt-in the read-only diagnostic passes all stages and live read-only planning options and shift times load. Connected browser flows, hosted CI and actual Linux-host acceptance remain outstanding. The Compose file runs development servers; a production build/deployment is a separate gate. The root just recipes, including `just run`, need a POSIX shell: on Windows they are meant for Git Bash or WSL, not the Command Prompt or PowerShell, and Windows use is untested.

## Webapp integration

The webapp is a plain Next.js App Router project. The home page, canonical month/station selection with complete read-only employee inspection, and monthly configuration (availability, wishes and dated staffing demand with a weekly pattern) are implemented, with controlled browser evidence. Generation of the full month with transient job states and the review of its schedule, with import and download of portable files and its explicit publication and clear, are implemented. Recurring settings and templates are not part of the application; optimization controls are omitted. Wishes are stored but do not influence generation. On the test database the project tables and the [prepared example inputs](examples.md#input-data-and-boundary-context) exist. Live checks on 2026-10-02 at revision `8089e0e`, through the running Compose API against the test database:

| Check (command)                                                    | Expected                                            | Actual                                     |
| ------------------------------------------------------------------ | --------------------------------------------------- | ------------------------------------------ |
| `GET /planning/options?year=2026&month=1`                          | The two example stations                            | `BSP-A`, `BSP-B`                           |
| `GET /employees` for both stations, each month January–June        | Complete inspection, jumper pool associated         | 57 employees, jumper pool 429, every month |
| `TimeOfficeService.read_generation_input`, January–June            | Complete input; no roster work                      | Built every month; 0 assignments, 0 wishes |
| `POST /demand/pattern` then `PUT /demand`, then `GET /demand`      | Twelve station months saved and read back unchanged | Identical for all twelve                   |
| `PUT` then `DELETE /availability/…` and `/wishes/…`                | Saved, read back, removed; tables empty afterwards  | `200`, read back, `204`; both tables empty |
| `PUT /availability/…` for an employee outside the configured units | Rejected                                            | `422`                                      |

Unrelated units, employees, plans and roster rows, and the two older project tables the API no longer reads (`StaffSchedulingMinimalStaffing`, `StaffSchedulingObjectiveWeights`), were counted before and after preparation and are unchanged.

## Solver and schedule check

`POST /generation` runs the solver for one full month in a background job; `GET /generation` reports the latest job, and every found schedule carries the independent [schedule check](../architecture/solver.md#result). The solver implements every agreed hard rule, including trusted context around the month; inputs exclude wishes and in-month roster work. Live runs through the running Compose API against the prepared test database, both example stations, 120-second limit, one run each:

| Month (date)              | Solver status | Duties | Check        | Findings | Open items                                           | Scores (health events, balance minutes, surplus intermediate) |
| ------------------------- | ------------- | ------ | ------------ | -------- | ---------------------------------------------------- | ------------------------------------------------------------- |
| January 2026 (2026-10-02) | `feasible`    | 1055   | `accepted`   | 0        | After-month boundary (next run), annual free Sundays | 65, 2529, 182                                                 |
| June 2026 (2026-10-02)    | `feasible`    | 1096   | `incomplete` | 0        | Blocking: no trusted context for May 27–31           | 93, 5028, 235                                                 |

In both runs the reported objective equals the weighted total of the recomputed scores; the relative gap is large (0.98–1.00) because the proven bound is weak. January's preceding context is the prepared December context. June's following context (July 1–3) was checked; June stays incomplete until an accepted May schedule is supplied as its context, which the six-month example sequence does. The first June run was infeasible: the prepared July context left no professional able to work the June 30 night (a fourth night in a row, or a duty inside the 48-hour recovery). The solver's diagnostic named this shortage, and the context was corrected by removing three trusted July 3 night duties; no rule was relaxed.

Jobs are lost on API restart. Monthly runs are independent; the coordinated six-month example files are pending. The application writes key-scoped saves to the project tables (availability, wishes, demand) and, only through explicit publication and clear, the worked rows of the stations' target plans.

## Review, import and export

**Prüfen** reviews the latest generated or imported schedule; `ScheduleBundle` validates imports and renders the four portable files, and the example tests validate and re-solve bundle folders without TimeOffice ([examples and reproduction](examples.md#bundle-files)). Live check on 2026-10-02 through the running Compose instance against the prepared test database:

| Check                                                                       | Expected                                    | Actual                                                                     |
| --------------------------------------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------- |
| `POST /generation`, January 2026, both example stations, 120 s              | A found schedule, reviewed automatically    | `feasible`, check `accepted`, 1059 duties, 0 findings                      |
| `GET /review?month=2026-01&stations=427,428` of the webapp                  | Review page with summary, grid and accounts | `200`; 57 employees, staffing of both stations                             |
| Webapp `/review/files/{name}` for all four files                            | Attachments of the reviewed bundle          | `200`; 233 kB input, 183 kB result, 160 kB schedule, 69 kB employee tables |
| Example validator (`check_examples`) on the downloaded folder, January only | Accepted single month of both stations      | No problem; open: following month's start, annual free Sundays             |

The pair passed the same validation as an import. A single month cannot show the sequence checks; they are covered by the offline tests until the six accepted months exist. Messages of findings and the API's import details are English; the webapp names import problems in German. The review is lost on API restart and is not a saved library.

The redesigned pages were checked read-only against the same prepared database through the running Compose webapp at revision `22d1c6c` (page loads only; no write was triggered):

| Check                                           | Expected                                          | Actual                                                                                                             |
| ----------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| All six pages for January 2026, BSP-A and BSP-B | `200`, no webapp or API errors                    | `200` each; logs clean                                                                                             |
| **Mitarbeiter**, details of one employee        | Accounts in hours, no raw IDs or provenance       | 57 employees; _Soll 163:48 h_, credits _7:48 h · Genehmigte Abwesenheit_                                           |
| **Erstellen** with the latest January job       | Headline, fact row and review link                | _Dienstplan erstellt, Regeln eingehalten_, 1072 duties, **Dienstplan prüfen**                                      |
| **Prüfen** summary and grid                     | Status line, actions; transfers marked with codes | _Regeln eingehalten · Kann veröffentlicht werden_; 143 transfers, codes BSP-A/BSP-B on one line; no truncated name |

Live publication and clear through the redesigned confirmation panels were not repeated; their backend behaviour is unchanged and the panels are covered by the offline browser flows.

## Publication and clear

Publication writes the accepted schedule under review into the stations' target plans and clear removes it ([procedure](../user-guide/publication.md), [storage](../architecture/timeoffice.md#publication)). Live check on 2026-10-02 against the prepared test database, one writer, through the running Compose API and webapp. Before and after every step the target plans' rows were counted by kind, and all roster rows outside the example plans and the example plans' absence and context rows were checksummed:

| Step                                                                    | Expected                                              | Actual                                                                                          |
| ----------------------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| Generate January, both example stations, 120 s                          | Accepted schedule under review                        | `feasible`, `accepted`, 1059 duties, 0 findings                                                 |
| `POST /publication`                                                     | 1059 duties written and read back, nothing removed    | `200`; 1995 rows (one per segment), nights dated on their start, jumper duties in station plans |
| Read-only SQL after publishing                                          | No duty on an absence date; everything else unchanged | 0 such duties; 32307 other roster rows and 2272 example absence/context rows, checksums equal   |
| Generate January again                                                  | Published rows are not input                          | 0 in-month context duties; `accepted`, 1051 duties                                              |
| `POST /publication` with the first schedule's `received_at`             | Refused, no change                                    | `409` `changed`                                                                                 |
| `POST /publication` of the new schedule                                 | Replacement                                           | 1059 removed, 1051 published                                                                    |
| Webapp **Prüfen**, BSP-B only: clear cancelled, then confirmed          | Only BSP-B's duties removed                           | _Entfernt: 606 veröffentlichte Dienste_; BSP-A's rows and all checksums unchanged               |
| Webapp **Prüfen**, both stations: publication cancelled, then confirmed | Committed and read back                               | _Veröffentlicht: 1051 Dienste geschrieben und gelesen, 445 bisherige ersetzt_                   |
| `DELETE /publication`, both stations                                    | Targets empty again                                   | 1051 removed; every count and checksum equals the starting state                                |

Each publication and clear took about one second. A second live check on the same day, after publication was limited to rows marked `Info` = `StaffScheduling`, prepared three unmarked rows in BSP-A's January target first (a native wish on an employee's duty date, a weekend absence on another employee's duty date and a duty entered as if by hand) and removed them again at the end:

| Step                                                                                                           | Expected                                                       | Actual                                                                                                                                            |
| -------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `POST /publication` of an accepted January schedule (1056 duties)                                              | Refused for the absence, no change                             | `409` `conflict` naming the employee and date; all counts and checksums equal                                                                     |
| Remove the absence, publish again                                                                              | Published; wish and entered duty kept                          | 1056 duties in 2002 marked rows; the wish keeps `lfdNr` 1 and the duty that date is numbered 2–3; the entered duty unchanged and unmarked         |
| Two separate processes publish the same schedule at once                                                       | One commits, the other fails without a change, or both in turn | One committed (1056 replaced); the other was SQL Server's deadlock victim and returned `TimeOfficeConflict`; 1056 duties, no duplicate roster key |
| `DELETE /publication`, both stations                                                                           | Only marked duties removed                                     | 1056 removed; wish and entered duty kept                                                                                                          |
| Availability and wish `PUT`/`GET`/`DELETE` for one employee; demand of one station month saved again unchanged | Read back, removed; demand identical                           | Read back, both `204`, empty afterwards; 280 demand cells identical                                                                               |

After removing the prepared rows every count and checksum equalled the starting state. Insert-failure rollback and ambiguous targets were not provoked live; the offline adapter tests own them. Whether the TimeOffice client displays published duties without `TPlanPersonal` rows was not checked.

## Quality gates

The latest executed offline suite reports **123 passed** and one skipped (the committed examples, which do not exist yet), including the solver integration tests; no test is excluded to manufacture success. The removed solver plugin tests are replaced by the schedule-check boundary examples (`test_schedule_check.py`) and production solves (`test_solver.py`).

Webapp strict TypeScript and the native production build pass. The twenty-three controlled browser scenarios (selection/inspection, unavailable/incomplete reads, back navigation, the sidebar of implemented areas, year entry and the January default, mobile navigation, availability edit/reload/delete with wishes, failed availability save, demand save/reload/reset/pattern with per-cell change marks, invalid count, failed demand save, generation without result or with incomplete input, a running generation across navigation with busy rejection and its accepted schedule check, infeasible versus failed runs, review of a generated schedule with its status, collapsed technical details, jumper-pool transfer markers and downloads, import of a matching pair and rejection of a mismatched pair without losing the review, imported home changes and unknown origins in the grid, a schedule of another scope, publication and clear each cancelled and then confirmed, a publication refused after the schedule under review changed, a failed publication that changes nothing, and no publication of an incompletely checked schedule) pass through the real pages/API with fictional SQL results; these do not establish live TimeOffice or Microsoft SQL Server execution evidence.

Formatting, API Ruff/Pyright, all configured Git hooks and strict documentation builds pass. Webapp ESLint reports no findings. React Doctor passes with visible warnings: pnpm install hardening and the standard shadcn `ui/` variant exports. `just check` runs all independent offline gates, including browser flows, production build and docs, and retains a failing exit status.

## Retired material

The old API CLI, separate frontend Python launcher, archived backend and service case directories were removed. Their setup instructions, JSON-file recipes, VM installer, screenshots, duplicated guides and historical documentation are no longer published here. Git history preserves older versions. Current contracts live in the source and these references; no alternative legacy setup is supported.
