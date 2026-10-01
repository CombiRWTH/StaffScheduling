# Staff Scheduling

Hospital staff scheduling with a Next.js webapp, a FastAPI API and Google OR-Tools CP-SAT, developed at RWTH Aachen University with St. Marien-Hospital Düren and Pradtke GmbH. The API reads planning data from an external TimeOffice SQL Server.

## Quickstart

Install [Docker with Compose](https://docs.docker.com/compose/install/) and start Docker. Download/clone this repository, then create `.secrets/db_password` in its root containing only the supplied test database password. The tracked `.env` contains the non-secret connection settings. Keep the password file private.

From the repository root:

```sh
docker compose up --build --wait
```

Open <http://localhost:3000>; API documentation is at <http://localhost:8000/docs>. No host Python, Node, pnpm or just is needed. Stop with `docker compose down`; inspect with `docker compose logs --follow`. See the [step-by-step quickstart](docs/source/getting-started/quickstart.md) and [full installation guide](docs/source/getting-started/installation.md).

Health checks establish service liveness. Database operations need network/credentials, and the planning workflow has [known integration and solver limitations](docs/source/validation/index.md). Independently accepted example schedules remain pending.

## Documentation and development

- [Use the application](docs/source/user-guide/index.md), including [month/station selection and employee inspection](docs/source/user-guide/selection.md)
- [Architecture and contracts](docs/source/architecture/index.md)
- [Checks and dependency maintenance](docs/source/development/checks.md)
- [Documentation maintenance](docs/source/development/documentation.md), [reasoning outline](docs/source/validation/reasoning.md) and [example reproduction outline](docs/source/validation/examples.md)
- [Glossary](GLOSSARY.md) of domain terms and [architecture decision records](docs/adr/)
- [API](docs/source/architecture/api.md), [domain](docs/source/architecture/domain.md), [solver](docs/source/architecture/solver.md), [TimeOffice](docs/source/architecture/timeoffice.md)

`api/`, `webapp/` and `docs/` have separate manifests/locks; `data/` holds ignored runtime files. Development services use Compose with hot reload. Optional native tools support IDEs and quality checks via `just install` and `just check`; follow the installation guide for their prerequisites.

[Online documentation](https://combirwth.github.io/StaffScheduling/) is published from main. `just docs` serves the local checkout at <http://localhost:8001>; `just docs-check` builds strictly using the independent docs environment.
