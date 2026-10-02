# Installation

Follow the [quickstart](quickstart.md) for the shortest path. This guide covers complete setup, configuration and optional native tooling. Run commands from the repository root unless a service directory is stated.

## Prerequisites

| Task                                  | Required                                                                                               |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Start API and webapp                  | Docker Engine with Compose, just, repository files, database password, free ports 3000 and 8000        |
| Use TimeOffice-backed planning        | Network/VPN access to the configured SQL Server, authorized database user and compatible planning data |
| Clone or contribute                   | Git; a source archive is enough for running the app                                                    |
| Native API tools and Git hooks        | uv 0.12.21 and Python from `api/.python-version`                                                       |
| Native webapp tools and Prettier hook | Node from `webapp/package.json` and its pinned pnpm version                                            |
| Build/view documentation locally      | uv and the pinned Python                                                                               |

Running the services needs only Docker with Compose and just; the other tools are for native development. Install them for your system:

??? note "macOS"

    Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/), which includes Engine and Compose, and [just](https://just.systems/man/en/packages.html), for example with `brew install just`. Git comes with the Xcode command line tools (`xcode-select --install`).

??? note "Linux"

    Install [Docker Engine and the Compose plugin](https://docs.docker.com/engine/install/), or Docker Desktop, and [just](https://just.systems/man/en/packages.html) from your package manager or its prebuilt binaries. Allow your user to run Docker commands, for example through the [`docker` group](https://docs.docker.com/engine/install/linux-postinstall/).

??? note "Windows"

    Install [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) with Linux containers, and [just](https://just.systems/man/en/packages.html). The root just recipes need a POSIX shell, and `just precheck` uses Bash; they do not support the Command Prompt or PowerShell. Run them from [Git Bash](https://git-scm.com/downloads/win) or [WSL](https://learn.microsoft.com/en-us/windows/wsl/install); with WSL, enable Docker Desktop's WSL integration. Windows use is untested.

The Docker daemon must be running. The first build needs internet access to fetch images, OS packages and locked dependencies. Docker images contain Python, Node, uv, pnpm and Microsoft's ODBC Driver 18; these do not need host installations for Compose startup. Dedicated Linux-host and connected database acceptance are still pending; see [limitations](../validation/index.md).

## Verify the installation

Check that the tools are found and that Docker can run a container:

```sh
git --version
just --version
docker --version
docker compose version
docker run --rm hello-world
```

The last command prints a greeting from Docker. After you [obtain the repository](#obtain-the-repository), check the project's own prerequisites from its root:

```sh
just precheck
```

It warns when Docker with Compose is missing, and when just, uv, `python3.14`, Node or pnpm are missing or differ from the versions pinned in the project files and CI. The Git hook calls `python3.14` directly. Warnings do not stop it; it fails only if the [password file](#database-configuration) is missing. `just run` runs it first.

!!! tip "If a check fails"

    - **`command not found`**: the tool is not installed or not on `PATH`. Open a new terminal after installing it; on Windows, use Git Bash or WSL.
    - **`Cannot connect to the Docker daemon`**: start Docker Desktop, or the Docker service on Linux (`sudo systemctl start docker`).
    - **`permission denied` on the Docker socket (Linux)**: add your user to the `docker` group, then log out and in again.

## Obtain the repository

```sh
git clone https://github.com/CombiRWTH/StaffScheduling.git
cd StaffScheduling
```

Alternatively, extract the provided source archive. Keep `.env`, `compose.yaml`, `api/` and `webapp/` together. The repository contains both services; no second frontend checkout or installer is needed.

## Database configuration

The root `.env` is tracked and contains only non-secret connection settings. For another authorized target, edit `DB_SERVER`, `DB_NAME` and `DB_USER`. `DB_DRIVER` defaults to `ODBC Driver 18 for SQL Server`. Keep the password in the ignored `.secrets/db_password` file, never in a committed configuration file.

Create that file with your editor or file manager, containing the supplied password only, without quotes. Replace or empty it the same way later. On macOS/Linux, restrict access after creating it:

```sh
chmod 700 .secrets
chmod 600 .secrets/db_password
```

On Windows, restrict the folder/file to your user through its security properties. To use a different file, set `DB_PASSWORD_FILE` in your shell environment, where both `just precheck` and Compose read it. Compose also reads it from `.env`, but `just precheck` does not.

Compose reads `.env` and mounts the password at `/run/secrets/db_password`. Pydantic settings loads that file using `SECRETS_DIR=/run/secrets`. The adapter connects to an external TimeOffice Microsoft SQL Server; Compose does not provision a database or sample hospital data. Arrange the required network/VPN route, database permissions and planning scope with the database administrator. [TimeOffice reference](../architecture/timeoffice.md) describes the adapter, its project tables, the prepared units and the checklist for supporting another unit. A database without the project tables and a configured, prepared unit can pass the connectivity diagnostic but cannot serve planning pages.

The SQL engine is lazy: startup needs no database connection. An empty password file permits startup when credentials are unavailable. Database-backed operations return a sanitized `503` with the failing stage and recovery advice. `/status` reports only API liveness; `/api/health` on the webapp makes a real server-side API request. The browser uses Next routes/actions; `http://api:8000` is the internal server URL, not a browser address.

Use a hostname or IP in `DB_SERVER`, with a separate optional `DB_PORT` (default 1433). `DB_TIMEOUT_SECONDS` defaults to five seconds, accepts 1–30, and bounds individual DNS, login and query waits. The total diagnostic can include several waits. The adapter requires encrypted SQL connections and validates the server certificate by default. Arrange a certificate matching the configured hostname and a CA trusted by the container; an IP address works only when the certificate covers it. For a private CA, have the administrator install its public CA certificate into the API image trust store and rebuild. A server with a self-signed certificate, such as the current test server, fails with `certificate verify failed: self-signed certificate`; for that known server only, set `DB_TRUST_SERVER_CERTIFICATE=true` (the tracked `.env` does this). The connection stays encrypted but the server's identity is not verified, so use it only on a trusted network route. Encryption cannot be disabled.

With services running, execute the read-only diagnostic:

```sh
just connectivity
```

It runs `python -m app.timeoffice.database` in the API container and checks configuration, the installed driver, DNS, encrypted login and `SELECT 1`. It prints safe JSON, exits nonzero on failure and performs no application-table queries or writes. A connection failure means checking the VPN/network route, firewall/port, login and TLS trust with the administrator. Query failure means checking connectivity/schema/permissions. SQLAlchemy may also issue read-only server/session metadata queries when initializing the connection. The diagnostic does not establish planning-table permissions or dataset validity.

## Start, update and stop

```sh
just run
```

`just run` runs `just precheck`, then `docker compose up --build --wait`: it builds both images, starts the services in the background and waits for their health checks. `just stop` and `just logs` wrap `docker compose down` and `docker compose logs --follow`.

Open <http://localhost:3000> and <http://localhost:8000/docs>. Ports bind to loopback by default. `API_PORT`, `WEBAPP_PORT` and `BIND_ADDRESS` can override them. Source mounts support FastAPI and Next.js development reload. Changes to manifests, locks or Dockerfiles require rebuilding with `just run`. The webapp installs its frozen lock in a persistent dependency volume when it starts.

```sh
just logs
just stop
```

Named volumes hold webapp dependencies and Next build output. `just stop` is sufficient for ordinary shutdown.

The current Compose setup runs development servers and exposes their ports on the host. A production deployment, authentication and TLS termination are outside this setup; it is intended for the prepared development/test environment.

## Laptop ports

For a prepared laptop needing LAN access, deliberately bind the development services and choose free host ports:

```sh
BIND_ADDRESS=0.0.0.0 API_PORT=8000 WEBAPP_PORT=3000 just run
```

Use the laptop's address in the browser. Its VPN/firewall must allow both the SQL connection and the intended client access. Keep loopback defaults for local use. Separate checkouts/projects can set `COMPOSE_PROJECT_NAME` and ports; `DB_PASSWORD_FILE` selects a private password file. Keep machine-specific overrides in your shell environment, rather than committing them. These are Compose settings, not `NEXT_PUBLIC_` browser configuration.

## Optional native developer setup

Services still start through `just run`. Native environments support IDEs, dependency maintenance, checks and Git hooks.

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.12.21 and Node as declared in `webapp/package.json`. Then:

```sh
uv python install "$(cat api/.python-version)"
npm install --global pnpm@12.8.1 --allow-scripts=pnpm
python3.14 --version
pnpm --version
just install
```

The [pnpm installation](https://pnpm.io/installation) uses npm; npm 12 requires explicit approval of pnpm's installation scripts. Ensure uv's executable directory (`~/.local/bin` by default) and npm's global executable directory are on `PATH`, including in the editor/terminal that commits. `python3.14` must match `api/.python-version`, and pnpm must match `packageManager` in `webapp/package.json`.

`just install` frozen-installs API and webapp dependencies, installs Chromium for offline browser tests and installs the Git hook. Linux browser-test hosts also need `pnpm --dir webapp exec playwright install --with-deps chromium`; see [testing](../development/testing.md#staff-admin-browser-flows). It preserves existing configuration and secrets. On macOS/Linux, native code that imports `pyodbc` also needs a host unixODBC driver manager. For native SQL connections, install [Microsoft ODBC Driver 18](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server) for your platform. Compose already supplies both; no host SQL client is needed for container use. Select `api/.venv` for the Python IDE interpreter. Documentation has its own environment. See [code quality](../development/checks.md) for checks and dependency changes.

## Documentation setup

With uv and the pinned Python installed:

```sh
just docs
```

Open <http://localhost:8001>. Stop the documentation server with Ctrl+C. `just docs-check` performs a strict build into ignored `docs/site/`. Both recipes install the independent frozen docs environment as needed. Without just, use:

```sh
uv run --directory docs --frozen --python "$(cat api/.python-version)" mkdocs serve --dev-addr 127.0.0.1:8001
```

## Troubleshooting

For missing commands and Docker daemon or permission errors, see [if a check fails](#verify-the-installation).

| Symptom                                                    | Check or action                                                                                                      |
| ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `docker compose` unavailable or `--wait` unknown           | Install/update the Compose plugin using Docker's installation guide.                                                 |
| Password file missing / settings validation error          | Run `just precheck`; check the exact `.secrets/db_password` path and root `.env`; inspect `docker compose logs api`. |
| Port 3000 or 8000 already allocated                        | Stop the conflicting process or previous Compose instance, then retry.                                               |
| Build/download failure                                     | Check internet/proxy access and the first failing build step; retry `just run`.                                      |
| Container unhealthy                                        | Inspect `docker compose ps` and `docker compose logs api webapp`; health checks cover liveness only.                 |
| Healthy API, failing employee/configuration query          | Check VPN/network, server/database/user/password and SQL permissions; startup did not test these.                    |
| Native install/check/hook cannot find Python, Node or pnpm | Complete native prerequisites and correct the committing terminal/editor's `PATH`; rerun `just install`.             |
| Type/test gate fails after installation                    | Compare the [known failing checks](../validation/index.md#quality-gates); do not bypass the gate.                    |
