# Evidence and current limitations

This checkout provides a reproducible development foundation. Connected planning, independently accepted schedules and the final example dataset remain unfinished. These limits describe current code and executed checks; they are not promises inferred from visible controls.

## What this section proves

For evaluators and anyone deciding whether to rely on a result. The checks below cover the current foundation; offline canonical selection/inspection is verified, while no independently accepted example schedule or live TimeOffice end-to-end flow is claimed. [Reasoning and requirements](reasoning.md) will explain policy choices and evaluation; [examples and reproduction](examples.md) will document actual accepted deliverables. These two pages are outlines.

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

## Solver and publication

`POST /generation` runs the solver for one full month in a background job; `GET /generation` reports the latest job. A completed job reports the CP-SAT status, but no independent schedule check exists: every result is reported as `not_assessed`, never as accepted. Offline, the fictional dataset solves as `feasible` with audit findings, which shows that a solver success is not schedule acceptance. Inputs exclude wishes, existing roster work and month-boundary context. A live January run of both example stations returned `feasible` after the 60-second limit, with audit findings from the `rounds` early-shift rule, a special capability that the example data deliberately does not provide. Jobs are lost on API restart. Nine solver unit tests fail. Independent schedule acceptance, complete required policy correction, scoped publication/clear verification and coordinated six-month example files are pending.

The only database writes are key-scoped saves to the project tables (availability, wishes, demand). No publication path exists; scoped, checked publication and clear are a later slice.

## Quality gates

The latest executed offline suite reports **135 passed and nine failed**: seven preferred-block-length objective tests and two forward-rotation tests. Solver correction owns those failures. No failing test is excluded to manufacture success.

Webapp strict TypeScript and the native production build pass. The fourteen controlled browser scenarios (selection/inspection, unavailable/incomplete reads, back navigation, unsupported areas, year entry and the January default, mobile navigation, availability edit/reload/delete with wishes, failed availability save, demand save/reload/reset/pattern, invalid count, failed demand save, generation without result or with incomplete input, a running generation across navigation with busy rejection, infeasible versus failed runs) pass through the real pages/API with fictional SQL results; these do not establish live TimeOffice or Microsoft SQL Server execution evidence.

Formatting, API Ruff/Pyright, all configured Git hooks and strict documentation builds pass. Webapp ESLint reports no findings. React Doctor passes with visible warnings: pnpm install hardening and the standard shadcn `ui/` variant exports. `just check` runs all independent offline gates, including browser flows, production build and docs, and retains a failing exit status. It remains red for the nine solver failures.

## Retired material

The old API CLI, separate frontend Python launcher, archived backend and service case directories were removed. Their setup instructions, JSON-file recipes, VM installer, screenshots, duplicated guides and historical documentation are no longer published here. Git history preserves older versions. Current contracts live in the source and these references; no alternative legacy setup is supported.
