# Checks and tooling

Run the root `just` recipes from the repository root. Native prerequisites are in [installation](../getting-started/installation.md#optional-native-developer-setup).

| Path      | Owns                                                              |
| --------- | ----------------------------------------------------------------- |
| `api/`    | API dependencies and tools, including pre-commit in the dev group |
| `webapp/` | Node dependencies, Prettier configuration and tools               |
| `docs/`   | MkDocs, with its own uv manifest and lock                         |

Commit all three locks and install them frozen. Use Conventional Commits.

## Commands

| Recipe                          | Behavior                                                                                 |
| ------------------------------- | ---------------------------------------------------------------------------------------- |
| `just install`                  | Frozen installs, Chromium and the Git hook; keeps configuration and secrets.             |
| `just precheck`                 | Warns about missing tools or other versions; fails only if the password file is missing. |
| `just format`                   | Ruff formats the API; Prettier the webapp and shared docs/configuration.                 |
| `just format-check`             | Non-mutating Ruff and Prettier checks.                                                   |
| `just lint`                     | Ruff; ESLint with Next core web vitals and TypeScript rules.                             |
| `just quality`                  | Full React Doctor scan.                                                                  |
| `just typecheck`                | Strict Pyright and `tsc --noEmit`.                                                       |
| `just test [arguments...]`      | Offline API tests; arguments pass to pytest.                                             |
| `just test-browser`             | Staff-admin browser flows.                                                               |
| `just docs` / `just docs-check` | MkDocs server / strict build.                                                            |
| `just build`                    | Native production webapp build, including its type gate.                                 |
| `just connectivity`             | Read-only connection diagnostic in the running API container.                            |
| `just test-timeoffice`          | `timeoffice` tests in the API image against the authorized test database.                |
| `just check`                    | Format check, lint, quality, types, API and browser tests, build, strict docs.           |

`just check` runs every gate even when one fails, and returns nonzero if any failed. It needs only the native tools. `just run` runs `just precheck`, then builds and starts both hot-reloading services through the root Compose file; it needs Docker Compose.

Checks never rewrite source or refresh locks. `just test-timeoffice` rolls back unless `TIMEOFFICE_PREPARATION=apply` is set. To run pytest directly, use `uv run --frozen python -m pytest` from `api/`. See [testing](testing.md) for what each test owns.

## Runtime and upgrade policy

| Tool                    | Pin                                                                             |
| ----------------------- | ------------------------------------------------------------------------------- |
| Python                  | `api/.python-version`: 3.14.7; Docker uses the matching Bookworm image.         |
| Node                    | `webapp/package.json` engines: 26.10.0; CI reads this field.                    |
| uv                      | 0.12.21 in Docker, hooks and workflows; `required-version` accepts it or newer. |
| pnpm                    | `webapp/package.json` `packageManager`: 12.8.1.                                 |
| just                    | 1.58.0, tested; `just precheck` warns about other versions.                     |
| Ruff / Pyright / pytest | API manifest and lock: 0.16.10 / 1.1.414 / 9.1.1.                               |
| Prettier / React Doctor | Webapp manifest and lock: 3.9.9 / 0.9.14.                                       |
| TypeScript / ESLint     | 6.0.3 / 9.39.5, see the exceptions below.                                       |

Service manifests and locks are authoritative. Every Dockerfile and workflow that uses a changed pin must agree with it.

Upgrade to the newest stable releases, then run `just install` and `just check`. These exceptions remain:

| Held back        | Reason                                                                                   | Revisit when                             |
| ---------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------- |
| Python 3.14.8    | No uv managed download for macOS arm64; no official `python:3.14.8-slim-bookworm` image. | Both artifacts exist                     |
| TypeScript 7.0.2 | Next's TypeScript ESLint parser crashes reading `ModuleKind.Cjs`; it supports below 6.1. | Next's parser supports TypeScript 7      |
| ESLint 10.11.0   | Next's React plugin calls the removed `context.getFilename` API.                         | The Next plugin stack supports ESLint 10 |

Other tooling decisions:

- eslint-config-prettier's audit found no formatting conflicts in the lint configuration, so it is not a dependency. See [Next.js ESLint guidance](https://nextjs.org/docs/app/api-reference/config/eslint).
- pnpm 12 needs `webapp/pnpm-workspace.yaml` for project settings, even for one package. It approves only the `sharp` and `unrs-resolver` build scripts; there is no root workspace. See the [pnpm settings reference](https://pnpm.io/settings).
- API reload uses native `fastapi dev` from the `fastapi[standard]` extra. `watchdog` belongs only to the docs environment.

## Rules and contracts

Prefer framework, standard-library and dependency primitives. Keep one domain model, shallow feature modules and small interfaces. Validate external input and raise specific exceptions. Avoid speculative abstractions and blanket suppressions.

Ruff selects E/F/B/W/I/C4/PT/UP, stable FAST, security and path checks, and selected RUF/SIM/exception and D rules. D rules use the Google convention without requiring docstrings everywhere. Only tests allow S101. The exact codes are in `api/pyproject.toml`; preview and unsafe fixes are off.

Document public, domain and adapter contracts and non-obvious behavior: Google-style docstrings in Python, short JSDoc in TypeScript. Give a summary plus Args, Returns, Raises or side effects where useful. Clarify units, identifiers and failure semantics, but leave types to annotations. Obvious helpers, render components and tests need none.

React Doctor scans fully with one worker and no cache, supply-chain scan or score service. Errors block; warnings stay visible. See the [CLI reference](https://www.react.doctor/docs/reference/cli-reference).

## Known failing checks

See [current limitations](../validation/index.md#quality-gates) for the latest results.

## Configuration ownership

Root EditorConfig supplies shared editor settings. Ruff uses a line width of 120 and four spaces; Prettier uses width 120 and two spaces.

Prettier configuration and ignore patterns live in `webapp/`. Root recipes add the shared documentation and configuration paths explicitly. Each Docker service has its own build-context ignore file. Environments, build output, runtime data and credentials stay untracked.

## Tests and documentation

Test each responsibility at one level: units for local logic, integration for module boundaries, system flows for staff-admin behavior. [Testing](testing.md) lists the owners.

Documentation is a separate MkDocs Material project. Edit `docs/source/`, update `docs/mkdocs.yml` navigation when adding or removing a page, and run `just docs-check`. Generated `docs/site/` is disposable. Every change updates its affected documentation; see [maintaining documentation](documentation.md).

## CI and Git hooks

`.github/workflows/ci.yml` runs on pushes to `main`, pull requests into `main` and manual runs. Its six independent jobs are:

- Hooks, lint, quality and type checks (`Pre-commit Checks`).
- All offline API tests.
- The Next production build.
- The offline browser flows.
- Compose validation, both image builds and the ODBC driver check.
- The strict documentation build.

A failing job does not stop the others. Installs are frozen, actions are pinned to commits and permissions are read-only. CI uses no database credentials.

`main` requires the check `Pre-commit Checks`, reported by the `quality` job. Required checks are repository settings. If the job is renamed without changing them, pull requests into `main` wait forever.

`.github/workflows/docs.yml` publishes to the `gh-pages` branch after a strict build. It runs on `main` pushes that change `docs/`, `api/.python-version` or the workflow itself. Only this job has write permission, and its deployments are serialized. GitHub Pages must keep serving `gh-pages`.

`just install` installs the only Git hook, `pre-commit`, from the tracked `.pre-commit-config.yaml`. Re-run it after changing or moving the native environment; never commit the generated hook. The hooks check:

- The API and docs locks, without updating them.
- JSON and YAML syntax, merge-conflict markers and private keys.
- Debug statements, using `python3.14` through pre-commit's [language version override](https://pre-commit.com/#overriding-language-version) to parse the API's syntax.
- Ruff lint and format.
- Prettier, through the webapp's locked binary, on the same paths as `just format-check`. Root data folders are not formatted.
- End-of-file and trailing whitespace. These hooks fix files; restage the corrections before committing.

Hooks pin the same Ruff and uv versions as local installs. Run `just format` before committing, and all hooks with `uv run --project api --frozen pre-commit run --all-files`. Tests, types, builds and docs belong to `just check` and CI.
