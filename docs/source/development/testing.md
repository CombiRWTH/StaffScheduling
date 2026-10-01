# Testing

Run commands from the repository root after the [native tool installation](../getting-started/installation.md#optional-native-developer-setup). Docker is also needed for the isolated foundation smoke. [Current limitations](../validation/index.md) records failing gates.

## Unit responsibilities

`just test` runs the offline API suite, including tests marked `integration`; only explicitly external `timeoffice` tests are excluded by default. Solver constraint/objective tests own local rules. Settings tests own secret loading. `test_inspection_rules.py` owns the domain rule that adds only pools that station members call home. The foundation tests exercise API liveness without credentials, shared database error sanitization/TLS, driver/settings validation and diagnostic cleanup/read-only query behavior.

## Service and adapter integration

```sh
just smoke
```

The smoke builds and boots both development images with fake localhost database settings, an empty temporary secret file, a unique project, dynamically allocated loopback ports and a temporary `data/` directory. It verifies API liveness, an actual request through the Next `/api/health` handler, an actionable unavailable-database `503`, unavailable-API `503`, recovery, and host/container output readability after stop/recreation. Cleanup removes only its own containers, network, volumes and temporary data; failures produce logs and a nonzero exit. It uses Docker, curl and a POSIX shell, without host Python or Node. It also calls both published host ports. A failed smoke must not be treated as accepted startup.

FastAPI and Next source reload were checked separately with isolated source copies: editing each live bind mount changed its HTTP response without rebuilding. Host `.venv`, `node_modules`, `.next`, local environment files and secrets are excluded from image build contexts; container dependency/build volumes mask host directories.

## Staff-admin browser flows

Selection/inspection is the first automated flow. The other four families (configuration, generation/review, import/export, publication/clear) remain pending. The foundation smoke is a separate HTTP/system-boundary check.

```sh
just install
just test-browser
```

The locked `@playwright/test` runner uses Chromium; `just install` installs it alongside frozen dependencies. Linux browser hosts also need `pnpm --dir webapp exec playwright install --with-deps chromium`. Tests require native API/webapp tools and free loopback ports 18080/18081. The runner starts/stops its own API and Next development servers and refuses to reuse an existing process. No database credentials or Docker are needed for this flow. `just check` runs it as an independent offline gate; CI has a separate browser job so solver failures do not suppress it.

`webapp/tests/browser/selection.spec.ts` selects both fictional stations/full month, verifies pool context, one row per stable employee, MFA, dated origin/replacement memberships, target/actual/credit evidence, restrictions, search and unit filter. It changes month/stations, retains available stations, removes unavailable ones and checks empty/unavailable/incomplete states and recovery without old-scope/partial tables. URL-backed checkbox transitions are checked after navigation, using bounded waits. Further tests check that a subpage's back arrow returns to the overview with the selection, that unsupported areas are visible in the sidebar but not navigable, that year entry keeps the month and rejects out-of-range years, that a missing or invalid month redirects to January of the current year and invalid stations ask for a selection, and that the mobile navigation opens, keeps the selection and closes. Another `next dev` for `webapp/` must not be running, because Next.js allows one development server per project directory.

`api/tests/browser_server.py` overrides the adapter dependency only in the test process. `inspection_fixture.py` substitutes SQL query results; the production queries, complete inspection validation and HTTP routes remain in use. The fixture supplies fictional IDs/names/complete monthly declarations and deliberate failure months. This proves offline user interaction and canonical integration, not Microsoft SQL Server query execution, live account semantics or real employee data acceptance. Production never imports this fixture.

`api/tests/test_employee_inspection.py` owns source completeness, identity under renaming, MFA/multiple memberships, pool origin versus destination eligibility, explicit zero accounts, missing/duplicate facts, TimeOffice code translation (trimmed codes, ignored and unmapped absence codes, unmapped professions, foreign or missing target plans, blank unit names) and HTTP validation. These checks do not invoke the solver. Traces on failure are ignored under `webapp/test-results/`; inspect with `pnpm --dir webapp exec playwright show-trace <path>`.

## Live TimeOffice verification

With services running, `just connectivity` performs only configuration/ODBC/DNS/login/`SELECT 1` checks. It needs the authorized connection settings, private password and VPN/network/TLS prerequisites documented in [installation](../getting-started/installation.md#database-configuration). It never runs application queries. A successful diagnostic would prove basic connection/query access, not planning-table permissions or valid scheduling data.

`just test-timeoffice` runs only explicitly external tests. No such tests are present yet: pytest exits with status 5, which is a missing gate, not success. Later live checks must use a declared prepared test database, serialize writes and independently verify publication/recovery scope.

## Linux and clean-checkout checks

The foundation was built and exercised in Docker Desktop Linux arm64 containers on macOS, including ODBC Driver 18 imports, HTTP connectivity, reload and persistent outputs. A Linux amd64 API image also passed build/import/ODBC checks. These are container/platform checks, not an actual Linux-host run. Hosted CI and the prepared laptop's Linux startup, output permissions, VPN/firewall and live database acceptance remain final verification gates.

CI's container job invokes the same credential-free `just smoke`; its independent jobs still report known solver failures. To repeat foundation verification on a Linux host, frozen-install native tools, run `just check`, retain every failing result, and run the read-only diagnostic separately with authorized configuration. The production webapp build and the final clean-checkout system/data checks remain separate acceptance evidence.
