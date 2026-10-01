# Installation and startup

Install this repository once to work with both services. This guide describes the current monorepo migration; connected Compose startup and aligned runtime/tool pins are still being completed in the foundation pass.

## Prerequisites

- Git, `just`, `uv`, and Python matching `api/.python-version` (currently Python 3.12).
- Node.js and npm. The imported frontend CI uses Node 24.11.0; its dependencies are locked in `webapp/package-lock.json`.
- unixODBC for importing `pyodbc` on a native host, and Microsoft ODBC Driver 18 for SQL Server for live TimeOffice access. The API Dockerfile includes these Linux dependencies.
- Authorized SQL Server connection details and any required hospital network/VPN/DNS/firewall access for TimeOffice operations.

## Install

```sh
git clone https://github.com/CombiRWTH/StaffScheduling.git
cd StaffScheduling
just sync
cp api/.env.template api/.env
```

`just sync` installs the existing frozen Python lock, including developer/documentation dependencies, and the committed npm lock. It does not create credentials. Keep local configuration out of Git. If `api/.env` already exists, edit it rather than overwriting it.

Set `DB_SERVER`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` in `api/.env`. The API currently requires these settings at application import. Copying the template only supplies placeholders; it does not establish database access. The existing adapter sets `TrustServerCertificate=yes`; certificate verification and independent connection diagnostics remain foundation work. Use only an authorized test environment.

Optional solver settings are `SOLVER_MAX_TIME_SECONDS`, `SOLVER_NUM_SEARCH_WORKERS`, `SOLVER_RANDOM_SEED` and `SOLVER_LOG_SEARCH_PROGRESS`. Omit optional numeric fields instead of setting them to empty strings.

The webapp falls back to `webapp/config.template.json`. For local overrides copy it to ignored `webapp/config.json`. `casesDirectory: "cases"` resolves from `webapp/`; an absolute path is used as written. The default mode is `api`; the webapp does not start Python itself. Set the server-side environment variable `SOLVER_API_URL` when the API is not at `http://127.0.0.1:8000`.

## Start on the host

Run these commands in separate terminals from the repository root:

```sh
just api-dev
```

```sh
just webapp-dev
```

Open `http://localhost:3000`. Check API process liveness with `just health` or `http://localhost:8000/status`; API schemas are at `http://localhost:8000/docs`. Liveness does not verify TimeOffice connectivity or schedule validity. API process state and the solve lock are local to one process; use one worker and expect jobs to disappear on restart.

Both services run from their own directories. API output is currently written under `api/found_solutions/` and `api/processed_solutions/`; frontend files remain under `webapp/cases/`. These are different roots and are not automatically synchronized. The canonical API/UI reconciliation and portable exports are subsequent work.

For production-style webapp startup:

```sh
cd webapp
npm run build
npm start
```

## API container

The relocated API container can be built with `just build`; `just run` retains the existing API-only development container command. It mounts API source/tests and output directories and reads `api/.env`. It is not yet the final connected Compose entry point. Stop it with Ctrl-C. `just debug` exposes debugpy on port 5678; the root `.vscode/launch.json` maps the local `api/` directory to `/app`.

## CLI and checks

The retained CLI supports full-month TimeOffice-backed solves:

```sh
cd api
uv run python -m app.cli --help
uv run python -m app.cli solve <planning-unit-id> <start-date> <end-date>
```

Dates accept `YYYY-MM-DD` or `DD.MM.YYYY`. This command requires database access; historical JSON cases do not enable a working offline CLI solve.

Run `just lint`, `just format`, `just typecheck`, `just test`, `just webapp-build`, and `just docs-check` from the root. The existing root lint/type/test recipes check the API; frontend checks are `cd webapp && npm run lint` and `cd webapp && npx tsc --noEmit`. `just test` excludes integration-marked tests. Full unified quality and CI commands follow in the tooling/foundation pass.

## Connection failures

If startup reports missing settings, check that `api/.env` exists and that the command runs from `api/`. A missing ODBC library requires the native unixODBC runtime; a missing named SQL Server driver requires Driver 18. DNS/login/timeout failures require checking the authorized server address, network/VPN, firewall and credentials with the database owner. Do not paste credentials or connection strings into issue reports.

If the webapp cannot contact the API, verify `/status` directly and the webapp server's `SOLVER_API_URL`, then restart Next.js after changing its environment. If case selection is empty, inspect `casesDirectory` from the webapp working directory; it should not default to the Linux filesystem root `/cases`.

Endpoint errors in generation/progress/publication may reflect the [known integration gaps](webapp/solver-integration.md), rather than connectivity. The current historical cases and UI do not establish a verified scheduling workflow.
