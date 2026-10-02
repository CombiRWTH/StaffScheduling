# Checks and tooling

Run the root `just` recipes from the repository root. API dependencies and tools belong to `api/`; Node dependencies, Prettier configuration and tools belong to `webapp/`. MkDocs has an independent uv manifest/lock under `docs/`. Pre-commit is a shared development tool installed with the API dev group. Native prerequisites are in [installation](../getting-started/installation.md#optional-native-developer-setup). Commit both service locks and the documentation tooling lock, and install them frozen. Use Conventional Commits.

## Commands

| Recipe                          | Behavior                                                                                                      |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `just install`                  | Frozen API/webapp installs, Chromium and Git hooks. Existing configuration and secrets are preserved.         |
| `just precheck`                 | Warns about missing tools or versions differing from the pins; fails only if the password file is missing.    |
| `just format`                   | Ruff formats Python; Prettier formats supported webapp and root documentation/configuration files.            |
| `just format-check`             | Non-mutating Ruff and Prettier checks.                                                                        |
| `just lint`                     | Ruff and Next core web vitals/TypeScript ESLint rules.                                                        |
| `just quality`                  | Full local React Doctor scan; errors fail, warnings remain visible.                                           |
| `just typecheck`                | Strict Pyright and explicit strict `tsc --noEmit`.                                                            |
| `just test [arguments...]`      | All offline tests, including solver and adapter tests using fakes. Arguments pass to pytest.                  |
| `just test-browser`             | Controlled Chromium staff-admin flows through temporary Next.js/FastAPI servers.                              |
| `just docs` / `just docs-check` | Unified MkDocs server / strict build.                                                                         |
| `just build`                    | Native production webapp build, including its type gate.                                                      |
| `just connectivity`             | Explicit read-only external connection diagnostic in the running API container.                               |
| `just test-timeoffice`          | External-only tests; currently exits 5 because none exist.                                                    |
| `just check`                    | Runs format, lint, quality, types, offline API/browser tests, build and strict docs; fails if any gate fails. |

`just run` runs `just precheck`, then builds and starts both hot-reloading services through one root Compose file. The CI definitions cover independent offline gates. Diagnostic failure paths are verified; successful external connectivity and hosted CI execution remain pending. `just run` requires Docker Compose; `just check` requires the native tools only. Checks never rewrite source or refresh locks; builds and pytest may create ignored output.

Use `just test-timeoffice` only for explicitly authorized external-database tests; none currently exist. `just connectivity` checks basic access without calling application-table readers. See [testing](testing.md) for evidence and boundaries.

`just install` installs the Git pre-commit hook from the API development environment. Hooks check service locks without updating them, Ruff, Prettier, merge-conflict markers and file/private-key hygiene. EOF/trailing-whitespace hooks can fix files; restage their corrections before committing. Follow the [native prerequisites](../getting-started/installation.md#optional-native-developer-setup) before installing hooks. Debug-statement detection explicitly uses `python3.14` so it can parse the API’s modern Python syntax, using pre-commit’s [language version override](https://pre-commit.com/#overriding-language-version). The Prettier hook runs the webapp’s locked Prettier binary through Node on the same paths as `just format-check` (the webapp, docs sources and ADRs, MkDocs configuration, README, glossary, Compose file, `.github` and the hook configuration); data folders in the repository root are not formatted. Python formatting is handled by the Ruff hook. Hooks use the same pinned Ruff/uv versions as local installs. Use `just format` before committing. Run the full hook suite with `uv run --project api --frozen pre-commit run --all-files`. Full checks belong outside the commit hook. EditorConfig, Ruff (Python width 120, four spaces) and Prettier (width 120, two spaces) define shared editor settings; personal extensions are optional.

## Runtime and upgrade policy

| Tool                    | Pin                                                                                  |
| ----------------------- | ------------------------------------------------------------------------------------ |
| Python                  | `api/.python-version`: 3.14.7; Docker uses the matching official Bookworm image tag. |
| Node                    | `webapp/package.json` engines: 26.10.0; CI reads this same field.                    |
| uv                      | 0.12.21 is enforced in both uv manifests and matched by Docker/hooks/workflows.      |
| pnpm                    | `webapp/package.json`: 12.8.1.                                                       |
| just                    | 1.58.0, tested; `just precheck` warns about other versions.                          |
| Ruff / Pyright / pytest | API manifest and lock: 0.16.10 / 1.1.414 / 9.1.1.                                    |
| Prettier / React Doctor | Webapp manifest and lock: 3.9.9 / 0.9.14.                                            |
| TypeScript / ESLint     | 6.0.3 / 9.39.5, compatibility exceptions below.                                      |

Use newest stable releases when upgrading, then verify frozen installs, lint, types, tests, build and docs. Compatibility trials retained these temporary exceptions:

- Python 3.14.8: uv had no macOS arm64 managed download, and the matching official `python:3.14.8-slim-bookworm` image was unavailable. Revisit when both artifacts exist.
- TypeScript 7.0.2: Next's TypeScript ESLint parser crashed reading `ModuleKind.Cjs`. Its declared support is below 6.1; 6.0.3 passes lint initialization.
- ESLint 10.11.0: Next's React plugin crashed calling the removed `context.getFilename` API. 9.39.5 passes the same check. Upgrade when the Next plugin stack supports ESLint 10.

The effective Next.js core web vitals/TypeScript configuration was checked with eslint-config-prettier’s audit CLI: no enabled formatting conflicts were found, so no additional lint configuration dependency is needed. See [Next.js ESLint guidance](https://nextjs.org/docs/app/api-reference/config/eslint).

pnpm 12 requires `pnpm-workspace.yaml` for project settings even for a single package; this service-local file approves only `sharp` and `unrs-resolver` build scripts and declares no additional packages. There is no root Node workspace. See the [pnpm settings reference](https://pnpm.io/settings).

API reload uses native `fastapi dev`; there is no custom file watcher. `watchdog` belongs only to the separate docs MkDocs environment and is absent from the API lock. The API uses the conventional `fastapi[standard]` extra.

## Rules and contracts

Prefer installed framework, standard-library and dependency primitives. Keep one domain model, shallow feature modules and small interfaces that hide actual complexity. Validate external input, use specific exceptions with useful context, and test behavior at the boundary that owns it. Avoid speculative abstractions, blanket suppressions and duplicate tests.

Ruff retains E/F/B/W/I/C4/PT/UP, adds stable FAST/security/path checks and selected RUF/SIM/exception rules. Ruff's formatter owns quotes and line wrapping. Selected D rules check existing docstring structure with the Google convention, without demanding boilerplate on every module/helper. Tests alone allow S101 for assertions. The exact codes are in `api/pyproject.toml`; preview and unsafe fixes are disabled.

Use Google-style Python docstrings on public/domain/adapter contracts and non-obvious constraints: a concise summary plus Args, Returns, Raises or side effects where useful. Keep types in annotations. TypeScript uses concise JSDoc for exported contracts and non-obvious behavior, without repeating types. Clarify units, identifiers and failure semantics. Obvious private helpers, render components and tests need no ceremonial documentation.

React Doctor runs the installed binary with full scope, no cache, no supply-chain scan, no score service or crash reporting, one worker, and error severity blocking. Warning findings stay visible for feature work. A partial scan does not establish a passing gate. See the [CLI reference](https://www.react.doctor/docs/reference/cli-reference).

## Known failing checks

See [current limitations](../validation/index.md#quality-gates) for the latest results and remaining acceptance. `just check` runs format, lint, quality, types, offline API/browser tests, production webapp build and strict docs even when a gate fails; it returns nonzero if any gate fails.

## Configuration ownership

Python comes from `api/.python-version`; CI reads Node from `webapp/package.json` (`engines.node`). uv is enforced by `required-version`, pnpm by `packageManager`. Service locks and manifests are authoritative. Each Dockerfile/workflow consuming a changed pin must agree with it.

Root EditorConfig supplies shared editor settings. Ruff uses a Python line width of 120 and four spaces; Prettier uses width 120 and two spaces. Prettier configuration/ignore patterns live in `webapp/`; root recipes explicitly include shared documentation/configuration paths. Each Docker service has its own build-context ignore file. Environments, build output, runtime data and credentials remain untracked.

## Tests and documentation

Use focused unit tests for local rule logic, service integration tests for module boundaries and distinct system flows for staff-admin behavior. Avoid proving the same responsibility at every level. `api/tests/cp/` covers constraints/objectives; the solution writer/settings/foundation tests cover adapter/settings behavior. `just build` runs the native production webapp build; `just connectivity` is an explicit read-only external diagnostic. `just test-timeoffice` selects only external tests; none are implemented yet, so it currently exits with pytest’s no-tests status rather than proving live acceptance. Run `uv run python -m pytest` from `api/` for direct test execution, or use root `just test` with forwarded arguments.

Documentation is a separate locked project with MkDocs and Material. Edit `docs/source/`, update `docs/mkdocs.yml` navigation when adding/removing a page, and run `just docs-check`. Keep current instructions tied to source, preserve known limitations and remove obsolete instructions rather than publishing competing workflows. Generated `docs/site/` is disposable. Every implementation change updates its affected documentation; see [maintaining documentation](documentation.md) for section ownership and evidence rules. See [testing](testing.md) for verified foundation checks and pending system procedures.

## CI and Git hooks

`.github/workflows/ci.yml` is the monorepo CI entry point for main/handin-readiness pushes, PRs into main and manual runs. Its six independent jobs cover quality/hooks and types, all offline API tests, the Next production build, the offline browser flows, the Compose file and both image builds with the ODBC driver check, and strict documentation. Independent jobs ensure a known type failure does not prevent tests or docs from running. Service installs are frozen, action references are pinned to commits and validation permissions are read-only. CI needs no TimeOffice credentials and performs no connected database operations.

`.github/workflows/docs.yml` publishes only relevant main-branch pushes to the existing `gh-pages` branch after a strict docs build. Only that publishing job has repository write permission; its deployments are serialized. Docs no longer import API modules, so API-source-only changes do not trigger publication. GitHub Pages must continue serving the `gh-pages` branch.

The only installed Git hook is `pre-commit`, managed by `just install` and the tracked `.pre-commit-config.yaml`. There is no custom hooks directory or pre-push wrapper. Git's `*.sample` files are inactive. Re-run `just install` after changing/moving the native environment; do not commit the generated machine-specific hook. Full tests, types, builds and docs belong to shared commands/CI rather than blocking every local commit.

Required-check rules are repository settings; renaming workflows does not migrate those settings. When enabling this CI, select the new job checks instead of retired Quality/Webapp check names. Hosted workflow execution and dedicated Linux-host startup remain separate acceptance evidence.
