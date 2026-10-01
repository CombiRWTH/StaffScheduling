# Code quality

Run the root `just` recipes from the repository root. API dependencies and tools belong to `api/`; Node dependencies, Prettier configuration and tools belong to `webapp/`. MkDocs has an independent uv manifest/lock under `docs/`. Pre-commit is a shared development tool installed with the API dev group. Commit both service locks and the documentation tooling lock, and install them frozen. Use Conventional Commits.

## Commands

| Recipe                          | Behavior                                                                                            |
| ------------------------------- | --------------------------------------------------------------------------------------------------- |
| `just install`                  | Frozen API/webapp installs and Git hooks. Existing configuration and secrets are preserved.         |
| `just format`                   | Ruff formats Python; Prettier formats supported webapp and root documentation/configuration files.  |
| `just format-check`             | Non-mutating Ruff and Prettier checks.                                                              |
| `just lint`                     | Ruff and Next core web vitals/TypeScript ESLint rules.                                              |
| `just quality`                  | Full local React Doctor scan; errors fail, warnings remain visible.                                 |
| `just typecheck`                | Strict Pyright and explicit strict `tsc --noEmit`.                                                  |
| `just test [arguments...]`      | All offline tests, including solver and adapter tests using fakes. Arguments pass to pytest.        |
| `just docs` / `just docs-check` | Unified MkDocs server / strict build.                                                               |
| `just check`                    | Formatting, lint, quality, types, offline tests and strict docs. Stops on the first failing recipe. |

`just run` builds and starts both hot-reloading services through one root Compose file. Isolated smoke/diagnostics and full CI follow in the connected foundation work. Checks never rewrite source or refresh locks; builds and pytest may create ignored output.

Use `just test -m timeoffice` only for explicitly authorized external-database tests; none currently exist. Run `pnpm run build` from `webapp/` when checking a production build.

`just install` installs the Git pre-commit hook from the API development environment. Hooks check service locks without updating them, Ruff, Prettier and file/private-key hygiene. The Prettier hook uses the webapp configuration directly; Python formatting is handled by the Ruff hook. Hooks use the same pinned Ruff/uv versions as local installs. Use `just format` before committing. Full checks belong outside the commit hook. EditorConfig, Ruff (Python width 120, four spaces) and Prettier (width 120, two spaces) define shared editor settings; personal extensions are optional.

## Runtime and upgrade policy

| Tool                    | Pin                                                                                  |
| ----------------------- | ------------------------------------------------------------------------------------ |
| Python                  | `api/.python-version`: 3.14.7; Docker uses the matching official Bookworm image tag. |
| Node                    | `webapp/package.json` engines: 26.10.0; CI reads this same field.                    |
| uv                      | 0.12.21 is enforced in both uv manifests and matched by Docker/hooks/workflows.      |
| pnpm                    | `webapp/package.json`: 12.8.1.                                                       |
| just                    | 1.58.0, tested; documented prerequisite without an unused version file.              |
| Ruff / Pyright / pytest | API manifest and lock: 0.16.10 / 1.1.414 / 9.1.1.                                    |
| Prettier / React Doctor | Webapp manifest and lock: 3.9.9 / 0.9.14.                                            |
| TypeScript / ESLint     | 6.0.3 / 9.39.5, compatibility exceptions below.                                      |

Use newest stable releases when upgrading, then verify frozen installs, lint, types, tests, build and docs. The 2026-10-01 trials retained these temporary exceptions:

- Python 3.14.8: uv had no macOS arm64 managed download, and the matching official `python:3.14.8-slim-bookworm` image was unavailable. Revisit when both artifacts exist.
- TypeScript 7.0.2: Next's TypeScript ESLint parser crashed reading `ModuleKind.Cjs`. Its declared support is below 6.1; 6.0.3 passes lint initialization.
- ESLint 10.11.0: Next's React plugin crashed calling the removed `context.getFilename` API. 9.39.5 passes the same check. Upgrade when the Next plugin stack supports ESLint 10.

The effective Next.js core web vitals/TypeScript configuration was checked with eslint-config-prettier’s audit CLI: no enabled formatting conflicts were found, so no additional lint configuration dependency is needed. See [Next.js ESLint guidance](https://nextjs.org/docs/app/api-reference/config/eslint).

The pnpm lock was imported from npm before upgrading dependencies. pnpm 12 requires `pnpm-workspace.yaml` for project settings even for a single package; this service-local file approves only `sharp` and `unrs-resolver` build scripts and declares no additional packages. There is no root Node workspace. See the [pnpm settings reference](https://pnpm.io/settings).

API reload uses native `fastapi dev`; there is no custom file watcher. `watchdog` belongs only to the separate docs MkDocs environment and is absent from the API lock. The API uses the conventional `fastapi[standard]` extra.

## Rules and contracts

Prefer installed framework, standard-library and dependency primitives. Keep one domain model, shallow feature modules and small interfaces that hide actual complexity. Validate external input, use specific exceptions with useful context, and test behavior at the boundary that owns it. Avoid speculative abstractions, blanket suppressions and duplicate tests.

Ruff retains E/F/B/W/I/C4/PT/UP, adds stable FAST/security/path checks and selected RUF/SIM/exception rules. Q and ISC were removed because Ruff's formatter owns quotes and line wrapping. Selected D rules check existing docstring structure with the Google convention, without demanding boilerplate on every module/helper. Tests alone allow S101 for assertions. The exact codes are in `api/pyproject.toml`; preview and unsafe fixes are disabled.

Use Google-style Python docstrings on public/domain/adapter contracts and non-obvious constraints: a concise summary plus Args, Returns, Raises or side effects where useful. Keep types in annotations. TypeScript uses concise JSDoc for exported contracts and non-obvious behavior, without repeating types. Clarify units, identifiers and failure semantics. Obvious private helpers, render components and tests need no ceremonial documentation.

React Doctor runs the installed binary with full scope, no cache, no supply-chain scan, no score service or crash reporting, one worker, and error severity blocking. The trial completed all 325 files in about 1.7 seconds; warning findings stay visible for the feature work. A partial scan does not establish a passing gate. See the [CLI reference](https://www.react.doctor/docs/reference/cli-reference).

## Known failing checks

The full offline suite currently has 89 passes and nine failures: seven preferred-block-length tests and two forward-rotation tests. The same failures occur with the original lock/runtime. Solver correction owns them; no tests are excluded to hide them.

The webapp type check and production build still fail at the existing employee repository's `db.write()` mismatch. The employee inspection slice owns that correction. Lint and quality warnings are visible, and later canonical feature slices own their behavioral cleanup. `just check` remains failing until these defects are corrected.

Python’s service version file is consumed by uv, CI and root tooling setup. Node needs no separate version file: CI reads `engines.node` from the existing service manifest, as supported by [setup-node](https://github.com/actions/setup-node/blob/main/docs/advanced-usage.md#node-version-file). uv is enforced by `required-version`, pnpm by `packageManager`, and just is a documented prerequisite. Redundant Node/uv/just version files were removed. Root EditorConfig remains project-wide; all Prettier options and ignore patterns live in `webapp/`. Root recipes explicitly select shared documentation/configuration files instead of scanning environments and output directories.

## Runtime and container choice

Python 3.14 and Node 26 are retained because frozen installs, API typing, offline tests and development startup were checked against the baseline. Python 3.14 includes [interpreter and library improvements](https://docs.python.org/3.14/whatsnew/3.14.html), but this project has no measured runtime speedup. Most solver computation is performed by native OR-Tools. No experimental JIT or free-threaded interpreter is enabled.

[Node 26 is Current; Node 24 is LTS](https://nodejs.org/en/about/previous-releases). Current is acceptable for this bounded student project after compatibility checks. Prefer an LTS line for long-lived production use. There is no observed compatibility reason to revert Python to 3.12.

Dockerfiles use official Debian slim Python/Node images and readable version tags, frozen locks, cached dependency layers before source, exec-form startup and native development commands. The API includes Microsoft's ODBC driver and the development tools; unused compilers were removed. One development Compose file for API and webapp is sufficient. Documentation uses native MkDocs. A production deployment would need its own build/runtime requirements, rather than an unused production stage here. These choices follow [Docker build guidance](https://docs.docker.com/build/building/best-practices/) and [FastAPI container guidance](https://fastapi.tiangolo.com/deployment/docker/).

One root `.gitignore` covers generated files and secrets across services. Each service build context has its own `.dockerignore`; Docker does not apply a root ignore file to service-local contexts. Prettier's service-local ignore file serves its separate formatting purpose.
