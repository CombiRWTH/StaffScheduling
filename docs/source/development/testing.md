# Testing

Run commands from the repository root after the [native tool installation](../getting-started/installation.md#optional-native-developer-setup). Docker is also needed for the isolated foundation smoke. [Current limitations](../validation/index.md) records failing gates.

## Unit responsibilities

`just test` runs the offline API suite, including tests marked `integration`; only explicitly external `timeoffice` tests are excluded by default. Solver constraint/objective tests own local rules. Settings tests own secret loading. `test_inspection_rules.py` owns the domain rule that adds only pools that station members call home. `test_monthly_configuration.py` owns the NRW calendar and weekly-pattern expansion rules. `test_generation.py` owns the generation job (immediate acceptance, busy rejection, lock release after solver and input failures, sanitized errors) through `Generation` with substitute input and solver functions. The foundation tests exercise API liveness without credentials, shared database error sanitization/TLS, driver/settings validation and diagnostic cleanup/read-only query behavior.

## Service and adapter integration

```sh
just smoke
```

The smoke builds and boots both development images with fake localhost database settings, an empty temporary secret file, a unique project, dynamically allocated loopback ports and a temporary `data/` directory. It verifies API liveness, an actual request through the Next `/api/health` handler, an actionable unavailable-database `503`, unavailable-API `503`, recovery, and host/container output readability after stop/recreation. Cleanup removes only its own containers, network, volumes and temporary data; failures produce logs and a nonzero exit. It uses Docker, curl and a POSIX shell, without host Python or Node. It also calls both published host ports. A failed smoke must not be treated as accepted startup.

FastAPI and Next source reload were checked separately with isolated source copies: editing each live bind mount changed its HTTP response without rebuilding. Host `.venv`, `node_modules`, `.next`, local environment files and secrets are excluded from image build contexts; container dependency/build volumes mask host directories.

## Staff-admin browser flows

Selection/inspection, monthly configuration and generation are automated. Review, import/export and publication/clear remain pending. The foundation smoke is a separate HTTP/system-boundary check.

```sh
just install
just test-browser
```

The locked `@playwright/test` runner uses Chromium; `just install` installs it alongside frozen dependencies. Linux browser hosts also need `pnpm --dir webapp exec playwright install --with-deps chromium`. Tests require native API/webapp tools and free loopback ports 18080/18081. The runner starts/stops its own API and Next development servers and refuses to reuse an existing process. No database credentials or Docker are needed for this flow. `just check` runs it as an independent offline gate; CI has a separate browser job so solver failures do not suppress it.

`webapp/tests/browser/selection.spec.ts` selects both fictional stations/full month, verifies pool context, one row per stable employee, MFA, dated origin/replacement memberships, target/actual/credit evidence, constraints, search and unit filter. It changes month/stations, retains available stations, removes unavailable ones and checks empty/unavailable/incomplete states and recovery without old-scope/partial tables. URL-backed checkbox transitions are checked after navigation, using bounded waits. Further tests check that a subpage's back arrow returns to the overview with the selection, that unsupported areas are visible in the sidebar but not navigable, that year entry keeps the month and rejects out-of-range years, that a missing or invalid month redirects to January of the current year and invalid stations ask for a selection, and that the mobile navigation opens, keeps the selection and closes. Another `next dev` for `webapp/` must not be running, because Next.js allows one development server per project directory.

`webapp/tests/browser/configuration.spec.ts` is the configure flow. On **Verfügbarkeit** it saves a _Nur bestimmte Schichten_ entry with shifts and reason, reloads, edits it to _Urlaub_, checks that the native absence stays, saves and removes a wish without touching the availability entry, then saves a wish and checks that editing and deleting the availability entry leaves it in place, and confirms the empty day (with the New Year holiday label) after reload. A save for "Example Pool Three" fails deliberately: the error appears, no success message, and the entered type stays. On **Mindestbesetzung** it edits and resets a cell, saves Fachkraft and MFA demand on different dates, reloads both, previews a weekly pattern (the New Year holiday takes the holiday row, six dates listed), applies it to the unsaved grid, checks that each qualification keeps its own pattern and resets it. A count of `-1` is marked invalid, rejected by the API on save and kept for correction. A save for "Example Station South" fails deliberately and keeps the unsaved edit.

`webapp/tests/browser/generation.spec.ts` is the generate flow. It shows _Kein Ergebnis verfügbar_ before any run, refuses a month without saved staffing and an invalid time limit, each with a message and no job, and disables the start without a station. It then starts a real solve of the fictional June month, checks the visible scope and **Läuft**, has a second page loaded earlier start too and get the busy message, navigates to **Mitarbeiter** and back through the sidebar, and waits for **Abgeschlossen** with a solver status, **Prüfung: Noch nicht verfügbar** and no automatic publication. Finally a substituted August solve is reported as **Keine Lösung möglich** while a July solver crash is **Fehlgeschlagen** without its internal message.

`api/tests/browser_server.py` overrides the adapter dependency only in the test process. For generation it seeds staffing for Station North in June to August, solves June with the real solver and substitutes a crash (July) and an infeasible result (August) after a two-second run. `inspection_fixture.py` substitutes SQL query results; the production queries, complete inspection validation and HTTP routes remain in use. The fixture supplies fictional IDs/names/complete monthly declarations, deliberate failure months and failing write IDs. The project tables are an in-memory store that applies the adapter's scoped DELETE/INSERT parameters and restores its state when a transaction fails. This proves offline user interaction and canonical integration, not Microsoft SQL Server query execution, live account semantics or real employee data acceptance. Production never imports this fixture.

`api/tests/test_employee_inspection.py` owns source completeness, identity under renaming, MFA/multiple memberships, pool origin versus destination eligibility, explicit zero accounts, missing/duplicate facts, TimeOffice code translation (trimmed codes, ignored and unmapped absence codes, unmapped professions, foreign or missing target plans, blank unit names) and HTTP validation. These checks do not invoke the solver.

`api/tests/test_monthly_configuration.py` owns the scoped configuration writes: availability and wish saves/deletes touch only their employee and date, native absences survive, reasons and shifts read back, wishes stay separate, invalid employees/shifts fail before writing and a failed write leaves saved entries unchanged. It also checks dated demand round-trips per station month (including MFA and an explicitly empty month), rejection of pools, stations without a target plan and unknown shifts, count bounds, the validated pattern preview, the evidence-free employee list, the availability calendar and the HTTP `422` contract. Live SQL Server round-trips of these tables belong to prepared-data verification.

`api/tests/test_generation.py` also owns the generation input and HTTP contract. Through `TimeOfficeService.read_generation_input` over the fixture it checks that polluted worked roster rows (an unmapped shift in another plan, earlier output in the target plan) never become input while the approved absence stays, that only the selected station and its associated pool are units, that wishes, assignments, plans and capabilities are empty, that a station without saved staffing is refused, and that shift times and paid minutes come from the target-time segments (including an overnight night shift and a segment without paid minutes) or fail when missing. The fixture applies the roster query's own absence filter, so a query that read worked shifts would fail this test. Over HTTP it runs one real solve to `completed` with `not_assessed`, and checks `404` before any job and after a restart (a fresh job state), `422`/`409` without a job and `423` while busy.

Traces on failure are ignored under `webapp/test-results/`; inspect with `pnpm --dir webapp exec playwright show-trace <path>`.

## Live TimeOffice verification

With services running, `just connectivity` performs only configuration/ODBC/DNS/login/`SELECT 1` checks. It needs the authorized connection settings, private password and VPN/network/TLS prerequisites documented in [installation](../getting-started/installation.md#database-configuration). It never runs application queries. It passes against the current test server with `DB_TRUST_SERVER_CERTIFICATE=true` (self-signed certificate). That proves basic connection/query access, not planning-table permissions or valid scheduling data.

`just test-timeoffice` runs only explicitly external tests. No such tests are present yet: pytest exits with status 5, which is a missing gate, not success. Later live checks must use a declared prepared test database, serialize writes and independently verify publication/recovery scope.

## Linux and clean-checkout checks

The foundation was built and exercised in Docker Desktop Linux arm64 containers on macOS, including ODBC Driver 18 imports, HTTP connectivity, reload and persistent outputs. A Linux amd64 API image also passed build/import/ODBC checks. These are container/platform checks, not an actual Linux-host run. Hosted CI and the prepared laptop's Linux startup, output permissions, VPN/firewall and live database acceptance remain final verification gates.

CI's container job invokes the same credential-free `just smoke`; its independent jobs still report known solver failures. To repeat foundation verification on a Linux host, frozen-install native tools, run `just check`, retain every failing result, and run the read-only diagnostic separately with authorized configuration. The production webapp build and the final clean-checkout system/data checks remain separate acceptance evidence.
