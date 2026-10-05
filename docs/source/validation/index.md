# Evidence and current limitations

This checkout provides checked monthly generation, review, validated import, portable downloads and scoped publication to TimeOffice for stations `PE 77`, `PE 78`, `PE 79`, `PE 83`, `PE 85`, `PE 88` and `PE 337` with jumper pools `PE 68` and `PE 408`. The example schedules in `plaene/` cover January to June 2026 without wishes for all seven stations, planned together with both jumper pools. These limits describe current code and executed checks; they are not promises inferred from visible controls.

## What this section proves

For evaluators and anyone deciding whether to rely on a result. The table lists what was executed and what it showed; [reasoning and requirements](reasoning.md) explains the policy choices, and [examples and reproduction](examples.md) the committed schedules and how to check them without TimeOffice.

| Area           | Executed check                                                                                                                                                  | Result                                                                                                                          |
| -------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Startup        | Earlier checks (2026-10-02): image-built Compose startup, Next server to API connectivity, unavailable database and API states, Linux arm64 containers on macOS | Pass; a Linux amd64 API build includes ODBC Driver 18                                                                           |
| Connectivity   | Earlier check (2026-10-02): read-only database diagnostic against the test server, with the explicit `DB_TRUST_SERVER_CERTIFICATE` opt-in                       | Every stage passes                                                                                                              |
| Prepared input | `just test-timeoffice` (2026-10-05)                                                                                                                             | Both tests pass for all nine units: no preparation write changes a row and every readiness check is met                         |
| Selection      | `GET /planning/options` and `GET /employees` for each station and for all seven, January to June (2026-10-05); the **Mitarbeiter** page for all seven           | All seven stations offered; 20 to 28 employees per station with jumper pools 68 and 408, 96 for all seven, every month          |
| Generation     | Earlier `POST /generation` check (2026-10-02), January, stations 77/79, 300 s, through the Compose API                                                          | `feasible`, check `accepted`, 0 findings, 0 gaps                                                                                |
| Examples       | Example generation (2026-10-05), all seven stations, January to June without wishes, 1,800 s per month, chained context                                         | Every month `accepted` with 0 findings; gaps 484, 411, 461, 479, 588, 477; gap optima unproven ([results](examples.md#results)) |
| Bundles        | Every committed month read as an import and checked as a sequence (`check_examples`)                                                                            | No problem: digests, references, re-check, CSV renderings and month-to-month context agree                                      |
| Publication    | Earlier checks (2026-10-02): publish, replace, refuse on conflict, clear and restore on example units of the test database that have since been removed         | Every count and checksum outside the published rows unchanged; the starting state restored                                      |
| Offline gates  | `just check`: formatting, linting, types, API tests, 24 browser flows with fictional SQL results, production build, docs                                        | Pass (2026-10-05): 171 API tests and 24 browser tests, including the six all-station bundles                                    |

## Webapp integration

The webapp is a plain Next.js App Router project: month and station selection with complete read-only employee inspection, monthly configuration (availability, wishes and dated staffing demand with a weekly pattern), generation with transient job states, review with import and downloads, and explicit publication and clear. Recurring settings, templates and optimization controls are not part of the application. On the test database the project tables and the [prepared inputs](examples.md#input-data-and-boundary-context) exist.

## Solver and schedule check

`POST /generation` solves one full month in a background job, and every found schedule carries the independent [schedule check](../architecture/solver.md#result). The solver implements every agreed hard rule with trusted context around the month, relaxes only staffing through reported gaps, and optimizes six tiers as lexicographic stages. The seven-station examples use 1,800 seconds per month. Every gap stage remains `feasible`, with its count and proven lower bound listed in the [results](examples.md#results); neither gaps nor the other time-limited objective values are proven optimal. Results vary between runs, because the search is parallel and time-limited.

## Review, import and export

**Prüfen** reviews the latest generated or imported schedule. `ScheduleBundle` validates imports and renders the six portable files, and the example tests validate and re-solve bundle folders without TimeOffice ([bundle files](examples.md#bundle-files)). Findings and the API's import details are in English, while the webapp names import problems in German.

## Publication and clear

Publication writes the accepted schedule under review into the stations' target plans, and clear removes it ([procedure](../user-guide/publication.md), [storage](../architecture/timeoffice.md#publication)). Only rows marked `Info` = `StaffScheduling` are replaced. A conflicting absence is refused with `409`, and of two concurrent publications one commits while the other fails without a change. These live checks ran on the earlier example units and were not repeated on `PE 77` and `PE 79`; the backend behaviour is unchanged since then.

## Quality gates

`just check` runs every independent offline gate and keeps a failing exit status; no test is excluded to manufacture success. The browser flows use fictional SQL results, so they do not establish live TimeOffice behaviour.

## Limitations

- **Platforms.** Hosted CI and a Linux host were not checked here. The root recipes need a POSIX shell, so Windows use through Git Bash or WSL is untested. The Compose file runs development servers.
- **Transient state.** Generation jobs and the review are lost on API restart; the review is not a saved library.
- **Month chaining.** Each month is solved without the next month's demand, so a month's last duties can cause gaps at the next month's start (March, [explained](examples.md#input-data-and-boundary-context)). Annual free Sundays need the whole year and are never reported as passed.
- **Reproduction.** A rerun finds an equally valid schedule, not the same bytes or objective values.
- **Station transfers.** Station transfers through a replacement membership (Ersatz) are modelled and minimized, but only the jumper pool has replacement memberships in the example data, so the examples show none.
- **Wishes.** Wishes come from the project table; TimeOffice's own wish rows (`Wunschdienst`) are not read. Maximizing granted wishes first, or minimizing the largest number of denials, are alternatives to the adopted cubic fairness cost.
- **Publication display.** Whether the TimeOffice client displays published duties without `TPlanPersonal` rows was not checked.
- **Dependency hardening.** pnpm's `minimumReleaseAge` and `trustPolicy: no-downgrade` are not enabled, because the current lock does not satisfy them.

## Retired material

The old API CLI, the separate frontend launcher and the archived backend and case directories were removed, together with their guides. Git history preserves older versions; no alternative legacy setup is supported.
