# Staff Scheduling

Hospital staff scheduling with a Next.js webapp, a FastAPI API and Google OR-Tools CP-SAT, developed at RWTH Aachen University with St. Marien-Hospital Düren and Pradtke GmbH. The API reads planning data from an external TimeOffice SQL Server.

## Quickstart

Install [Docker with Compose](https://docs.docker.com/compose/install/) and start Docker. Download/clone this repository, then create `.secrets/db_password` in its root containing only the supplied test database password. The tracked `.env` contains the non-secret connection settings. Keep the password file private.

From the repository root:

```sh
docker compose up --build --wait
```

Open <http://localhost:3000>; API documentation is at <http://localhost:8000/docs>. No host Python, Node, pnpm or just is needed. Stop with `docker compose down`; inspect with `docker compose logs --follow`. See the [step-by-step quickstart](docs/source/quickstart.md) and [full installation guide](docs/source/installation.md).

Health checks establish service liveness. Database operations need network/credentials, and the planning workflow has [known integration and solver limitations](docs/source/limitations.md). Independently accepted example schedules remain pending.

## Documentation and development

- [Using the app](docs/source/usage.md)
- [Codebase overview](docs/source/development/overview.md)
- [Checks and dependency maintenance](docs/source/development/quality.md)
- [API](docs/source/reference/api.md), [domain](docs/source/reference/domain.md), [solver](docs/source/reference/solver.md), [TimeOffice](docs/source/reference/timeoffice.md)

`api/`, `webapp/` and `docs/` have separate manifests/locks; `data/` holds ignored runtime files. Development services use Compose with hot reload. Optional native tools support IDEs and quality checks via `just install` and `just check`; follow the installation guide for their prerequisites.

[Online documentation](https://combirwth.github.io/StaffScheduling/) is published from main. `just docs` serves the local checkout at <http://localhost:8001>; `just docs-check` builds strictly using the independent docs environment.
