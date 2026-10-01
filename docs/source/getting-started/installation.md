# Installation

Follow the [quickstart](quickstart.md) for the shortest path. This guide covers complete setup, configuration and optional native tooling. Run commands from the repository root unless a service directory is stated.

## Prerequisites

| Task                                  | Required                                                                                               |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Start API and webapp                  | Docker Engine with Compose, repository files, database password, free ports 3000 and 8000              |
| Use TimeOffice-backed planning        | Network/VPN access to the configured SQL Server, authorized database user and compatible planning data |
| Clone or contribute                   | Git; a source archive is enough for running the app                                                    |
| Use root task recipes                 | just, tested with 1.58.0                                                                               |
| Native API tools and Git hooks        | uv 0.12.21 and Python from `api/.python-version`                                                       |
| Native webapp tools and Prettier hook | Node from `webapp/package.json` and its pinned pnpm version                                            |
| Build/view documentation locally      | uv and the pinned Python; just for `just docs` recipes                                                 |

[Docker Desktop](https://docs.docker.com/compose/install/) includes Engine and Compose on macOS, Windows and Linux. Linux users can install Engine and the Compose plugin separately. The daemon must be running; the user must be able to run Docker commands. On Windows, use Linux containers. The root just recipes use a POSIX shell; use WSL for those recipes.

Verify the container prerequisites:

```sh
docker version
docker compose version
```

The first build needs internet access to fetch images, OS packages and locked dependencies. Docker images contain Python, Node, uv, pnpm and Microsoft's ODBC Driver 18; these do not need host installations for Compose startup. Dedicated Linux-host and connected database acceptance are still pending; see [limitations](../validation/index.md).

## Obtain the repository

```sh
git clone https://github.com/CombiRWTH/StaffScheduling.git
cd StaffScheduling
```

Alternatively, extract the provided source archive. Keep `.env`, `compose.yaml`, `api/`, `webapp/` and `data/` together. The repository contains both services; no second frontend checkout or installer is needed.

## Database configuration

The root `.env` is tracked and contains only non-secret connection settings. For another authorized target, edit `DB_SERVER`, `DB_NAME` and `DB_USER`. `DB_DRIVER` defaults to `ODBC Driver 18 for SQL Server`. Keep the password in the ignored `.secrets/db_password` file, never in a committed configuration file.

Create that file with your editor, containing the supplied password only, without quotes. On macOS/Linux, restrict access after creating it:

```sh
chmod 700 .secrets
chmod 600 .secrets/db_password
```

On Windows, restrict the folder/file to your user through its security properties. Do not overwrite an existing password during setup.

Compose reads `.env` and mounts the password at `/run/secrets/db_password`. Pydantic settings loads that file using `SECRETS_DIR=/run/secrets`. The adapter connects to an external TimeOffice Microsoft SQL Server; Compose does not provision a database or sample hospital data. Arrange the required network/VPN route, database permissions and planning scope with the database administrator. [TimeOffice reference](../architecture/timeoffice.md) describes the adapter and supplemental tables.

The SQL engine is lazy: startup needs no database connection. An empty password file permits startup when credentials are unavailable. Database-backed operations return a sanitized `503` with the failing stage and recovery advice. `/status` reports only API liveness; `/api/health` on the webapp makes a real server-side API request. The browser uses Next routes/actions; `http://api:8000` is the internal server URL, not a browser address.

Use a hostname or IP in `DB_SERVER`, with a separate optional `DB_PORT` (default 1433). `DB_TIMEOUT_SECONDS` defaults to five seconds, accepts 1–30, and bounds individual DNS, login and query waits. The total diagnostic can include several waits. The adapter requires encrypted SQL connections and validates the server certificate. Arrange a certificate matching the configured hostname and a CA trusted by the container; an IP address works only when the certificate covers it. For a private CA, have the administrator install its public CA certificate into the API image trust store and rebuild. Do not disable encryption or certificate verification to bypass failures.

With services running, execute the read-only diagnostic:

```sh
docker compose exec -T api python -m app.timeoffice.database
# Equivalent when just is installed:
just connectivity
```

It checks configuration, the installed driver, DNS, encrypted login and `SELECT 1`. It prints safe JSON, exits nonzero on failure and performs no application-table queries or writes. A connection failure means checking the VPN/network route, firewall/port, login and TLS trust with the administrator. Query failure means checking connectivity/schema/permissions. SQLAlchemy may also issue read-only server/session metadata queries when initializing the connection. The diagnostic does not establish planning-table permissions or dataset validity.

## Start, update and stop

```sh
mkdir -p data/found_solutions data/processed_solutions
docker compose up --build --wait
docker compose ps
```

Open <http://localhost:3000> and <http://localhost:8000/docs>. Ports bind to loopback by default. `API_PORT`, `WEBAPP_PORT` and `BIND_ADDRESS` can override them. Source mounts support FastAPI and Next.js development reload. Changes to manifests, locks or Dockerfiles require rebuilding with the same startup command. The webapp installs its frozen lock in a persistent dependency volume when it starts.

```sh
docker compose logs --follow
docker compose down
```

`data/` is shared by both services and initially contains only `.gitkeep`. Retained file-based screens use `data/cases/`; solver compatibility exports use `data/found_solutions/` and `data/processed_solutions/`. Prepare the two output directories before startup as shown above; `just run` does this too. Runtime files are ignored. The API maps them under `/project/data/`; the webapp maps the same root under `/data/`. Container shutdown preserves them. Exported compatibility files are not independently accepted hand-in schedules.

Named volumes hold webapp dependencies and Next build output. Do not delete `data/` as a troubleshooting step. `docker compose down` is sufficient for ordinary shutdown.

The current Compose setup runs development servers and exposes their ports on the host. A production deployment, authentication and TLS termination are outside this setup; it is intended for the prepared development/test environment.

## Laptop ports and output permissions

For a prepared laptop needing LAN access, deliberately bind the development services and choose free host ports:

```sh
BIND_ADDRESS=0.0.0.0 API_PORT=8000 WEBAPP_PORT=3000 docker compose up --build --wait
```

Use the laptop's address in the browser. Its VPN/firewall must allow both the SQL connection and the intended client access. Keep loopback defaults for local use. Separate checkouts/projects can set `COMPOSE_PROJECT_NAME`, ports and `DATA_DIR`; `DB_PASSWORD_FILE` selects a private password file. Keep machine-specific overrides in your shell environment, rather than committing them. These are Compose settings, not `NEXT_PUBLIC_` browser configuration.

Linux bind mounts preserve numeric ownership. The current containers run as root; prepare the host output directories as your user and check host readability after writing. If existing directories are owned by another user, arrange narrowly scoped ownership correction for those output directories; do not use `chmod 777`. Stop/recreation preserves host data; removing the webapp dependency/build volumes is separate from removing outputs. Jobs and the solve lock remain in one API process and disappear on reload/restart; there is no automatic job recovery.

## Optional native developer setup

Service startup remains through Compose. Native environments support IDEs, dependency maintenance, checks and Git hooks.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.12.21, Node as declared in `webapp/package.json`, and [just](https://github.com/casey/just#installation). Then:

```sh
uv python install "$(cat api/.python-version)"
npm install --global pnpm@12.8.1 --allow-scripts=pnpm
python3.14 --version
pnpm --version
just install
```

The [pnpm installation](https://pnpm.io/installation) uses npm; npm 12 requires explicit approval of pnpm's installation scripts. Ensure uv's executable directory (`~/.local/bin` by default) and npm's global executable directory are on `PATH`, including in the editor/terminal that commits. `python3.14` must match `api/.python-version`, and pnpm must match `packageManager` in `webapp/package.json`.

`just install` frozen-installs API and webapp dependencies and installs the Git hook. It preserves existing configuration and secrets. On macOS/Linux, native code that imports `pyodbc` also needs a host unixODBC driver manager. For native SQL connections, install [Microsoft ODBC Driver 18](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server) for your platform. Compose already supplies both; no host SQL client is needed for container use. Select `api/.venv` for the Python IDE interpreter. Documentation has its own environment. See [code quality](../development/checks.md) for checks and dependency changes.

## Documentation setup

With uv, the pinned Python and just installed:

```sh
just docs
```

Open <http://localhost:8001>. Stop the documentation server with Ctrl+C. `just docs-check` performs a strict build into ignored `docs/site/`. Both recipes install the independent frozen docs environment as needed. Without just, use:

```sh
uv run --directory docs --frozen --python "$(cat api/.python-version)" mkdocs serve --dev-addr 127.0.0.1:8001
```

## Troubleshooting

| Symptom                                                    | Check or action                                                                                                         |
| ---------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Docker daemon unavailable                                  | Start Docker Desktop/Engine; verify `docker version`.                                                                   |
| `docker compose` unavailable or `--wait` unknown           | Install/update the Compose plugin using Docker's installation guide.                                                    |
| Password file missing / settings validation error          | Check the exact `.secrets/db_password` path and root `.env`; inspect `docker compose logs api`.                         |
| Port 3000 or 8000 already allocated                        | Stop the conflicting process or previous Compose instance, then retry.                                                  |
| Build/download failure                                     | Check internet/proxy access and the first failing build step; retry the startup command.                                |
| Container unhealthy                                        | Inspect `docker compose ps` and `docker compose logs api webapp`; health checks cover liveness only.                    |
| Healthy API, failing employee/configuration query          | Check VPN/network, server/database/user/password and SQL permissions; startup did not test these.                       |
| Missing route or empty case/schedule selector              | Consult [limitations](../validation/index.md); removed case files and integration gaps are not an installation failure. |
| Native install/check/hook cannot find Python, Node or pnpm | Complete native prerequisites and correct the committing terminal/editor's `PATH`; rerun `just install`.                |
| Type/test gate fails after installation                    | Compare the [known failing checks](../validation/index.md#quality-gates); do not bypass the gate.                       |
