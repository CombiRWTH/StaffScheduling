# Keep the command surface minimal

Staff administrators use the webapp, and developers start the application with `docker compose up --build --wait`. Everything else is a small set of root `just` recipes that wrap native service commands: installation, the individual quality gates, `check`, docs and explicit diagnostics. CI runs the same recipes, so there is one command contract. The API has no command-line interface.

## Considered Options

- **Keep the API CLI.** Rejected: it served the file-based case workflow, which the webapp and canonical API endpoints replace. A second entry point would duplicate domain behavior and need its own tests and documentation.
- **Native and containerized launchers for each service, plus a separate development mode.** Rejected: one hot-reloading Compose setup starts both services the same way on every machine, and native tools remain for IDEs, checks and docs.
- **A recipe for every Docker or service command.** Rejected: thin wrappers around single commands hide the real tool without adding behavior.

## Consequences

New operations go into the webapp and API, not into scripts. `run`, `stop` and `logs` are the only convenience wrappers, around Compose; any other new recipe must combine steps or be needed by CI.
