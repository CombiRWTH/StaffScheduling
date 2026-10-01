# Getting started for developers

Follow the shared [installation and startup guide](../installation.md) for both services, local configuration, CLI commands and checks.

The [codebase overview](codebase-overview.md) describes the canonical backend domain, solver and adapter. The [webapp developer reference](../webapp/developer-guide.md) describes the imported frontend structure; those legacy layers are retained for relocation and will be simplified in subsequent feature slices.

See [migration notes](monorepo-migration.md) for source provenance, documentation disposition and checks. Do not infer verified end-to-end behavior from the imported UI or historical screenshots.

Use the shared [code quality commands and standards](code-quality.md). The root recipes run both services; offline tests include the solver integrations.
