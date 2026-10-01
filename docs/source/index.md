# Staff Scheduling

Staff Scheduling combines a Next.js webapp, a FastAPI application and an OR-Tools CP-SAT solver in one repository. TimeOffice access is isolated in the Python adapter.

Start with [installation and startup](installation.md), then choose:

- [User guide](user-view/index.md): the planning problem and configuration concepts.
- [Webapp workflow](webapp/user-guide.md): the imported views and screenshots.
- [Developer guide](developer-view/index.md): domain, API, database and solver references.
- [Migration notes](developer-view/monorepo-migration.md): layout, provenance and verification limits.

The monorepo migration preserves the imported application's behavior. The [integration limits](webapp/solver-integration.md) identify legacy UI assumptions still requiring reconciliation. Historical examples do not substitute for independently validated schedules.

[Historical documentation](collection-of-old-docs/index.md) records earlier implementations and is separate from current installation instructions.
