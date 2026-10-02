# Keep the API and webapp in one monorepo

The backend and the frontend started as separate repositories with their own documentation, CI and startup helpers. They are one application: the webapp only presents data from the API, so an API contract change and its webapp change belong in one commit. This repository therefore holds both services as `api/` and `webapp/`, with one README, one installation guide, one MkDocs site, one Compose file and one CI workflow. The backend repository is the history base; the frontend was imported from a committed state of its main branch.

## Considered Options

- **Two repositories.** Rejected: every contract change needed coordinated releases, and documentation, CI and startup drifted apart, which presented one application as two projects.
- **One project with shared tooling at the root.** Rejected: FastAPI and Next.js each have conventional layouts and tool configuration. Each service keeps its own manifest, lock, Dockerfile and tool settings, and the root only orchestrates.

## Consequences

Root files (`Justfile`, `compose.yaml`, `.pre-commit-config.yaml`, `.github/`) call into the service directories instead of duplicating their configuration. Imported frontend history is not part of this repository.
