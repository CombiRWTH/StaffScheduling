# Architecture and contracts

The repository contains a Python API, a Next.js webapp and one MkDocs documentation project. FastAPI owns the canonical scheduling domain and solver; TimeOffice-specific SQL, identifiers and translations stay in its adapter. The selection/employee slice uses direct canonical server reads; remaining imported views still contain compatibility code.

## Who this section serves

For developers and technical reviewers tracing responsibilities and data flow. This is a source-inspected map, not proof of connected operation. Read the [domain](domain.md) for scheduling terms and units, [API](api.md) for HTTP boundaries, [solver](solver.md) for the model and [TimeOffice adapter](timeoffice.md) for external dependencies.

## Repository map

```text
.
├── compose.yaml              # API/webapp development startup and mounts
├── .env                      # non-secret database connection settings
├── .secrets/                 # ignored local password file
├── Justfile                  # shared install/check/docs/Compose recipes
├── api/
│   ├── app/
│   │   ├── main.py           # FastAPI construction and runtime lifespan
│   │   ├── settings.py       # environment and secret loading
│   │   ├── dependencies.py   # access to process-local services/jobs/lock
│   │   ├── routers/          # solve job routes and DTOs
│   │   ├── domain/           # canonical Pydantic scheduling models
│   │   ├── employees/        # selection/employee routes and complete inspection validation
│   │   ├── validation/       # dataset integrity checks
│   │   ├── solver/           # CP-SAT building, execution and audit
│   │   └── timeoffice/       # database reads, mappings and compatibility exports
│   ├── tests/
│   ├── pyproject.toml
│   ├── uv.lock
│   └── .python-version
├── webapp/
│   ├── src/
│   │   ├── app/              # App Router pages, route-local components, /api/health
│   │   ├── components/       # shell, planning picker and ui/ primitives
│   │   └── lib/              # server-only API fetches, response types, scope parsing
│   ├── tests/browser/        # Playwright staff-admin flows
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── pnpm-workspace.yaml   # single-package settings/build approvals
├── docs/
│   ├── source/               # documentation content
│   ├── mkdocs.yml
│   ├── pyproject.toml
│   └── uv.lock
└── data/                     # persistent runtime files; empty on checkout
```

Service Dockerfiles live alongside their manifests. Generated environments, dependencies, `docs/site/`, webapp build output, secrets and runtime data are ignored. There is no root Node workspace or Python package.

## Request and solve flow

```mermaid
flowchart LR
    Browser[Browser] --> Webapp[Next.js webapp]
    Webapp --> API[FastAPI routes]
    API --> Adapter[TimeOffice service]
    Adapter <--> SQL[(External SQL Server)]
    Adapter --> Dataset[Validated SchedulingDataset]
    Dataset --> Solver[CP-SAT solver]
    Solver --> Result[Solution and audit]
    Result --> Jobs[In-memory job result]
    Jobs --> API
    Result --> Export[Compatibility JSON files]
```

Next.js server components call the API at `API_URL`; Compose sets it to `http://api:8000`. Browser traffic enters the webapp. `api/app/main.py` builds the SQLAlchemy engine, TimeOffice service, solver service, in-memory job store and one solve lock. Shutdown disposes the engine.

`POST /solve/` accepts a month and units, reserves the lock and starts a background task. Database fetching, dataset validation, solver work and compatibility export run through a worker thread. Polling returns job execution state and the eventual solution. Database publication is separate from generation. The [API reference](api.md) describes the precise route boundaries.

## Where to make a change

| Change                                  | Start here                                                                |
| --------------------------------------- | ------------------------------------------------------------------------- |
| API request/response or job lifecycle   | `api/app/routers/`, `dependencies.py`, `main.py`                          |
| Scheduling concept or dataset integrity | `api/app/domain/`, `api/app/validation/`                                  |
| Constraint/objective or solving         | `api/app/solver/cp_sat/`, `solver/config.py`, `solver/service.py`         |
| TimeOffice query or mapping             | `api/app/timeoffice/reading/`, `mapping/`, `service.py`                   |
| Screen behavior                         | `webapp/src/app/<route>/` and shared `webapp/src/components/`             |
| Webapp API calls and response types     | `webapp/src/lib/api.ts`, `webapp/src/lib/types.ts`                        |
| Runtime/dependency pins                 | service manifests/locks, Dockerfiles and consuming workflow/tool settings |
| Documentation                           | `docs/source/` and `docs/mkdocs.yml`                                      |

Trace the real callers before changing a boundary. Keep TimeOffice terminology inside the adapter and use the canonical backend models for new behavior. Read [domain](domain.md), [solver](solver.md), [TimeOffice](timeoffice.md) and [development checks](../development/checks.md) for details. The [limitations](../validation/index.md) page records remaining compatibility work.

## Selection and inspection boundary

The webapp follows plain App Router conventions. Pages are server components that read `month`/`stations` from `searchParams`, load data through `lib/api.ts` and pass it to small client components. `lib/scope.ts` validates the URL and loads the month's stations; stations unavailable in the month are dropped by a server redirect. The picker only changes the URL. `app/employees/` loads all selected stations together inside a Suspense boundary keyed by scope, so a new scope shows its loading state instead of the previous result. Search, filter and expanded details are local interaction state. Backend `employees/` validates completeness; the concrete TimeOffice adapter resolves target plans and reads membership/master/account/absence sources and prepared evidence. Only home and employee inspection are implemented; the sidebar shows every other area greyed out as not yet supported, without routes.

The offline browser fixture substitutes SQL query results, while using the actual FastAPI routes, TimeOffice readers/mappers and Next.js pages. It is test infrastructure, never a production data fallback. [Testing](../development/testing.md#staff-admin-browser-flows) describes reproduction and limitations.
