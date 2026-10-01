# Evidence and current limitations

This checkout provides a reproducible development foundation. Connected planning, independently accepted schedules and the final example dataset remain unfinished. These limits describe current code and executed checks; they are not promises inferred from visible controls.

## What this section proves

For evaluators and anyone deciding whether to rely on a result. The checks below cover the current foundation; no independently accepted example schedule or connected end-to-end flow is claimed. [Reasoning and requirements](reasoning.md) will explain policy choices and evaluation; [examples and reproduction](examples.md) will document actual accepted deliverables. These two pages are outlines.

## Startup and connectivity

Image-built development Compose startup, actual Next-server/API HTTP connectivity, bounded unavailable-database/API states, persistent output recreation and separate source reload passed in Linux arm64 containers on macOS. A Linux amd64 API build/import check includes ODBC Driver 18. `/status` reports API liveness; Next `/api/health` checks API process connectivity. Neither claims database readiness. Explicit read-only diagnostics failed at the encrypted connection stage for the configured test target. Live TimeOffice access, connected staff-admin flows, hosted CI and actual Linux-host acceptance remain outstanding. The Compose file runs development servers; a production build/deployment is a separate gate.

## Webapp integration

The imported webapp retains file-based case discovery under `data/cases/`, compatibility-shaped repositories and several endpoint/schema assumptions. The runtime data directory starts empty. Repository names containing `lowdb` remain in code, but the LowDB dependency has been removed; several of those modules now call HTTP APIs.

The backend does not supply the old `/fetch`, `/insert`, `/delete`, multi-solve or phase-progress contracts. The UI expects `/schedules/metadata`, whereas `GET /schedules` currently returns an empty placeholder list. Employee/configuration schemas and schedule formats still need reconciliation. Templates/global settings, file-library operations and imported progress displays must not be treated as verified canonical features.

## Solver and publication

Jobs and the solve lock are process-local; use one API process. Jobs disappear on reload/restart. A completed job can contain an infeasible, unknown or invalid model result. Independent schedule acceptance, complete required policy correction, scoped publication/clear verification and coordinated six-month example files are pending.

The current publication endpoint translates legacy variables and performs a transactional database write, but strengthened input/scope checks and connected acceptance are unfinished. A transaction alone does not prove the chosen roster is correct or safely scoped. Current compatibility JSON exports are not the final portable input/result/CSV bundle contract.

## Quality gates

The latest executed offline suite reports **93 passed and nine failed**: seven preferred-block-length objective tests and two forward-rotation tests. Solver correction owns those failures. No failing test is excluded to manufacture success.

Webapp strict TypeScript reports TS2339 at `src/infrastructure/repositories/lowdb-employee.repository.ts:19`: `write` is absent from the returned object type. Employee inspection migration owns the correction. The Linux-container production build compiles and then fails at this same type gate; production build acceptance remains outstanding.

Formatting, API Ruff/Pyright, all configured Git hooks and strict documentation builds pass. Webapp ESLint has zero errors and 13 warnings; React Doctor warnings remain visible. `just check` now runs all independent offline gates, including production build, docs and credential-free Compose smoke, and retains a failing exit status. It remains red for the existing employee type/build and nine solver failures.

## Retired material

The old API CLI, separate frontend Python launcher, archived backend and service case directories were removed. Their setup instructions, JSON-file recipes, VM installer, screenshots, duplicated guides and historical documentation are no longer published here. Git history preserves older versions. Current contracts live in the source and these references; no alternative legacy setup is supported.
