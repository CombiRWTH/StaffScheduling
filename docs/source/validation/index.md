# Evidence and current limitations

This checkout provides a reproducible development foundation. Connected planning, independently accepted schedules and the final example dataset remain unfinished. These limits describe current code and executed checks; they are not promises inferred from visible controls.

## What this section proves

For evaluators and anyone deciding whether to rely on a result. The checks below cover the current foundation; offline canonical selection/inspection is verified, while no independently accepted example schedule or live TimeOffice end-to-end flow is claimed. [Reasoning and requirements](reasoning.md) will explain policy choices and evaluation; [examples and reproduction](examples.md) will document actual accepted deliverables. These two pages are outlines.

## Startup and connectivity

Image-built development Compose startup, actual Next-server/API HTTP connectivity, bounded unavailable-database/API states, persistent output recreation and separate source reload passed in Linux arm64 containers on macOS. A Linux amd64 API build/import check includes ODBC Driver 18. `/status` reports API liveness; Next `/api/health` checks API process connectivity. Neither claims database readiness. Explicit read-only diagnostics failed at the encrypted connection stage for the configured test target. Live TimeOffice access, connected staff-admin flows, hosted CI and actual Linux-host acceptance remain outstanding. The Compose file runs development servers; a production build/deployment is a separate gate.

## Webapp integration

The webapp is a plain Next.js App Router project. Only the home page and canonical month/station selection with complete read-only employee inspection are implemented, with controlled browser evidence. Monthly configuration, minimum staffing, generation, review/export/publication, recurring settings and templates appear greyed out in the sidebar as not yet supported and have no pages; optimization is omitted. Selection requires explicit prepared monthly credit/restriction evidence; no live table provisioning or inspection has been performed.

## Solver and publication

The solver engine is not reachable through the API; its unit tests run offline, nine currently failing. Generation jobs, independent schedule acceptance, complete required policy correction, scoped publication/clear verification and coordinated six-month example files are pending.

No publication or other database write path exists; scoped, checked publication and clear are a later slice.

## Quality gates

The latest executed offline suite reports **115 passed and nine failed**: seven preferred-block-length objective tests and two forward-rotation tests. Solver correction owns those failures. No failing test is excluded to manufacture success.

Webapp strict TypeScript and the native production build pass. The five controlled browser scenarios (selection/inspection, unavailable/incomplete reads, unsupported areas, year entry and malformed selection URLs, mobile navigation) pass through the real pages/API with fictional SQL results; these do not establish live TimeOffice or Microsoft SQL Server execution evidence.

Formatting, API Ruff/Pyright, all configured Git hooks and strict documentation builds pass. Webapp ESLint reports no findings. React Doctor passes with visible warnings: pnpm install hardening, the planning picker's control-flow complexity and the standard shadcn `ui/` variant exports. `just check` now runs all independent offline gates, including browser flows, production build, docs and credential-free Compose smoke, and retains a failing exit status. It remains red for the nine solver failures.

## Retired material

The old API CLI, separate frontend Python launcher, archived backend and service case directories were removed. Their setup instructions, JSON-file recipes, VM installer, screenshots, duplicated guides and historical documentation are no longer published here. Git history preserves older versions. Current contracts live in the source and these references; no alternative legacy setup is supported.
