# Installation and startup

## Start with Docker

Install Docker with Compose and just (tested with 1.58.0). Docker must be running. Run commands from the repository root; local Node, Python, uv and pnpm are unnecessary for container startup.

The committed root `.env` contains the test database server, database name and user. Keep passwords out of it. Create `.secrets/db_password` containing the test database password supplied separately. This directory is ignored by Git; restrict access to it on your machine. Compose mounts the file at `/run/secrets/db_password`, and Pydantic settings reads it automatically. Existing secret files are never overwritten by installation.

```sh
just run
```

This builds and starts the API and webapp and waits for their health checks. Open <http://localhost:3000>; API schemas are at <http://localhost:8000/docs>. The single Compose file uses fixed ports 3000 and 8000, native `fastapi dev` and Next.js development reload. Edit application source and the running services reload. Dependency changes require rebuilding; webapp startup installs the frozen lock into its persistent dependency volume.

The webapp reaches the API through the server-side `SOLVER_API_URL=http://api:8000` environment variable. Browser requests use the webapp's routes. Both services mount the root `data/` directory. It starts empty except for `.gitkeep`; retained file-based planning features create `data/cases/` on use, and API exports create their output directories there. `just stop` removes containers without deleting these files or dependency volumes. Use `just logs` for service output.

`/status` checks process liveness, not database connectivity or schedule validity. Access to the configured TimeOffice SQL Server is required for database operations. API jobs and the solve lock belong to one process and disappear on reload or restart. The imported planning screens still have the [documented integration limits](webapp/solver-integration.md).

## IDE support and dependency maintenance

Install uv 0.12.21 and the Node version declared in `webapp/package.json`. Install the pinned Python and pnpm before running `just install`:

```sh
uv python install "$(cat api/.python-version)"
npm install --global pnpm@12.8.1 --allow-scripts=pnpm
python3.14 --version
pnpm --version
just install
```

Ensure uv’s Python executable directory (`~/.local/bin` by default) and npm’s global executable directory are on `PATH`, including in the terminal or editor that commits. `python3.14` must report the version in `api/.python-version`; pnpm must report the `packageManager` version in `webapp/package.json`. This follows the [pnpm installation guide](https://pnpm.io/installation); npm 12 requires explicit approval of pnpm’s native installation scripts. `just install` installs frozen API and webapp dependencies and Git hooks. It preserves existing configuration and secret files.

Start development services with `just run`; Compose provides both hot-reloading servers. No host service launch recipes are provided.

Use ordinary uv and pnpm commands from their service directories to change dependencies, then commit their updated manifests and locks. Root just recipes provide [shared quality checks](developer-view/code-quality.md), including all offline solver tests; known solver/type failures remain visible.

## Documentation

`just docs` installs the frozen docs lock as needed and runs native MkDocs at <http://localhost:8001>. `just docs-check` builds strictly. These commands need uv and the declared Python runtime; Docker is unnecessary for documentation. Configuration, dependencies and lock live in `docs/`; Markdown and assets are in `docs/source/`. Generated `docs/site/` contains disposable HTML, CSS and JavaScript and is ignored. MkDocs has no dependency on the API environment.
