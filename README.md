# Staff Scheduling

Staff Scheduling is a hospital staff scheduling application developed at RWTH Aachen University with St. Marien-Hospital Düren and Pradtke GmbH. A Next.js webapp provides planning views, while a FastAPI application reads TimeOffice data and generates schedules with Google OR-Tools CP-SAT.

This repository contains one project:

- `api/`: Python application, canonical domain, solver, TimeOffice adapter and tests.
- `webapp/`: Next.js application.
- `docs/`: shared user and developer documentation, built with MkDocs.

## Install and start

See the [installation guide](docs/source/installation.md) for prerequisites, configuration and troubleshooting.

```sh
# Create ignored .secrets/db_password with the supplied test database password.
just run
```

Open <http://localhost:3000>. The API exposes interactive documentation at <http://localhost:8000/docs>.

Startup requires Docker with Compose and just. One root Compose file provides native API and webapp hot reload on ports 8000 and 3000. Frozen Python and pnpm locks use verified runtime/tool pins. The imported UI still has legacy file and endpoint assumptions; see [integration limits](docs/source/webapp/solver-integration.md) before generating or publishing schedules. Historical case files have been removed; validated hand-in schedules remain pending.

## Development

Use `just run` for development through Compose. For IDE support, dependency maintenance and quality checks, install the pinned runtimes, uv and pnpm, then run `just install`.

```sh
just format-check
just lint
just quality
just typecheck
just test
just docs-check
```

`just test` includes all offline solver/service integration tests. Only actual external-database tests use the separate `timeoffice` marker. See [code quality](docs/source/developer-view/code-quality.md) for the unified `just check` gate, compatibility exceptions and known failures.

[Online documentation](https://combirwth.github.io/StaffScheduling/) is published from main. Run `just docs` to view the working documentation locally using uv and Python; its dependencies stay in `docs/`.
