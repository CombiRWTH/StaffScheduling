# Staff Scheduling

Staff Scheduling is a hospital staff scheduling application developed at RWTH Aachen University with St. Marien-Hospital Düren and Pradtke GmbH. A Next.js webapp provides planning views, while a FastAPI application reads TimeOffice data and generates schedules with Google OR-Tools CP-SAT.

This repository contains one project:

- `api/`: Python application, canonical domain, solver, TimeOffice adapter, tests and historical cases.
- `webapp/`: Next.js application and imported example files.
- `docs/`: shared user and developer documentation, built with MkDocs.

## Install and start

See the [installation guide](docs/installation.md) for prerequisites, configuration and troubleshooting.

```sh
just sync
cp api/.env.template api/.env
# Set the TimeOffice connection settings in api/.env.
just api-dev
```

In another terminal at the repository root, run `just webapp-dev` and open <http://localhost:3000>. The API exposes interactive documentation at <http://localhost:8000/docs>.

The current migration uses the existing Python and npm locks. Connected Compose startup and the tooling transition follow in the foundation pass. The imported UI still has legacy file and endpoint assumptions; see [integration limits](docs/webapp/solver-integration.md) before generating or publishing schedules. Example files are historical inputs, not validated hand-in schedules.

## Development

```sh
just lint
just typecheck
just test
just webapp-build
just docs-check
```

`just test` currently excludes integration-marked tests; run `cd api && uv run python -m pytest -m integration` to include those separately. Existing failing checks and migration verification are recorded in [the migration notes](docs/developer-view/monorepo-migration.md).

[Online documentation](https://combirwth.github.io/StaffScheduling/) is published from main. Run `just docs` to view the working documentation locally.
