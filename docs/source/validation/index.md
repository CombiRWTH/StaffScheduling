# Evidence and current limitations

This checkout provides a reproducible development foundation with checked monthly generation. Review, publication and the final example dataset remain unfinished. These limits describe current code and executed checks; they are not promises inferred from visible controls.

## What this section proves

For evaluators and anyone deciding whether to rely on a result. The checks below cover the current foundation and generation; a live January schedule was accepted by the independent check, but no exported example bundle or live end-to-end publication is claimed. [Reasoning and requirements](reasoning.md) explains policy choices and evaluation; [examples and reproduction](examples.md) will document the accepted deliverables.

## Startup and connectivity

Image-built development Compose startup, actual Next-server/API HTTP connectivity, bounded unavailable-database/API states, persistent output recreation and separate source reload passed in Linux arm64 containers on macOS. A Linux amd64 API build/import check includes ODBC Driver 18. `/status` reports API liveness; Next `/api/health` checks API process connectivity. Neither claims database readiness. The configured test server presents a self-signed certificate; with the explicit `DB_TRUST_SERVER_CERTIFICATE` opt-in the read-only diagnostic passes all stages and live read-only planning options and shift times load. Connected browser flows, hosted CI and actual Linux-host acceptance remain outstanding. The Compose file runs development servers; a production build/deployment is a separate gate.

## Webapp integration

The webapp is a plain Next.js App Router project. The home page, canonical month/station selection with complete read-only employee inspection, and monthly configuration (availability, wishes and dated staffing demand with a weekly pattern) are implemented, with controlled browser evidence. Generation of the full month with transient job states is implemented. Review/export/publication, recurring settings and templates appear greyed out in the sidebar as not yet supported and have no pages; optimization is omitted. Wishes are stored but do not influence generation. On the test database the project tables and the [prepared example inputs](examples.md#input-data-and-boundary-context) exist. Live checks on 2026-10-02 at revision `8089e0e`, through the running Compose API against the test database:

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

Jobs are lost on API restart. Monthly runs are independent; scoped publication/clear and the coordinated six-month example files are pending. The only database writes of the application are key-scoped saves to the project tables (availability, wishes, demand); no publication path exists yet.

## Quality gates

The latest executed offline suite reports **91 passed**, including the solver integration tests; no test is excluded to manufacture success. The removed solver plugin tests are replaced by the schedule-check boundary examples (`test_schedule_check.py`) and production solves (`test_solver.py`).

Webapp strict TypeScript and the native production build pass. The fourteen controlled browser scenarios (selection/inspection, unavailable/incomplete reads, back navigation, unsupported areas, year entry and the January default, mobile navigation, availability edit/reload/delete with wishes, failed availability save, demand save/reload/reset/pattern, invalid count, failed demand save, generation without result or with incomplete input, a running generation across navigation with busy rejection and its accepted schedule check, infeasible versus failed runs) pass through the real pages/API with fictional SQL results; these do not establish live TimeOffice or Microsoft SQL Server execution evidence.

Formatting, API Ruff/Pyright, all configured Git hooks and strict documentation builds pass. Webapp ESLint reports no findings. React Doctor passes with visible warnings: pnpm install hardening and the standard shadcn `ui/` variant exports. `just check` runs all independent offline gates, including browser flows, production build and docs, and retains a failing exit status.

## Retired material

The old API CLI, separate frontend Python launcher, archived backend and service case directories were removed. Their setup instructions, JSON-file recipes, VM installer, screenshots, duplicated guides and historical documentation are no longer published here. Git history preserves older versions. Current contracts live in the source and these references; no alternative legacy setup is supported.
