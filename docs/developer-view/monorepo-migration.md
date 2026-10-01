# Monorepo migration

The backend repository and Git history remain the project base. The backend source was relocated from commit `5c232935f2bd0b55fb2dd9472b8909d9e5b1f708`; the frontend was imported from committed main `a2b7b36f226f7bb4f0993ac6cc17f9d1807df88c`. Only committed frontend files were used. Local frontend patches and case deletions were not imported.

## Layout and behavior

The Python application now lives directly in `api/app/`, with FastAPI in `app/main.py`, shared runtime dependencies in `app/dependencies.py`, routers in `app/routers/`, and the retained CLI in `app/cli.py`. Run it from `api/` with `uv run python -m app.cli`; the application is no longer installed as a distribution. Domain, solver, validation and TimeOffice modules retain their behavior. Python dependencies and tool configuration stay in `api/pyproject.toml` and `api/uv.lock`.

The frontend uses one `webapp/src/` root, including `app/`, `components/`, `features/`, `lib/`, `di/`, the imported implementation layers and `proxy.ts`. The `@/*` alias maps to `./src/*`. Native Next.js dev/start scripts replace the Python auto-launch wrapper. Existing frontend architecture and domain assumptions remain for later feature slices.

Backend cases and archives are under `api/cases/` and `api/legacy/`; frontend committed cases remain under `webapp/cases/`. No overlapping case set was overwritten. The safe webapp template uses relative `cases`, avoiding the unintended absolute `/cases` path on Linux. API output paths remain relative to the API working directory. Historical cases are not validated submission exports.

## Documentation disposition

| Original material | Disposition |
| --- | --- |
| Backend README, developer setup, light setup and web interface overview | Merged into one root README and shared installation guide; old pages point to the shared guide and accurately describe offline limits. |
| Backend domain, solver, database, configuration and how-to references and images | Retained with relocated paths/import examples; API route inventory checked against actual OpenAPI. |
| Existing `collection-of-old-docs/` | Retained as historical material, separate from current startup instructions. |
| Frontend README and docs index | Merged into the project overview and webapp documentation index. |
| Frontend user guide and screenshots | Workflow sections retained in `docs/webapp/user-guide.md`; competing installer/setup sections retired and JSX wrappers converted to Markdown. Screenshots describe the imported UI. |
| Frontend developer guide | Implementation reference retained under `docs/webapp/`; directory/alias examples updated and duplicate documentation deployment retired. |
| Frontend underlying data | Retained as a legacy file-format reference; shared-file assumptions explicitly limited. |
| Frontend solver integration and troubleshooting | Useful current guidance merged into concise pages; original details retained under historical documentation with explicit compatibility warnings. |
| Frontend Nextra package, app, configs, lock and Pages workflow | Retired; one root MkDocs project and existing deployment workflow remain. |
| Independent installer, workstation batch file and auto-launch scripts | Retired; root commands and native service startup replace them. |

Root orchestration, existing CI working directories/cache paths, pre-commit selectors and debugger mappings follow the relocated service directories. Runtime upgrades, npm-to-pnpm migration, unified quality gates, connected Compose startup, independent database diagnostics and persistence acceptance remain the next foundation work. No new database or solver behavior was introduced here.

## Verification

The frozen Python lock installs as an application and passes lock consistency checks. Backend Ruff, formatting and strict Pyright pass. FastAPI import/lifespan, `/status`, OpenAPI and CLI `--help` pass without a live database connection.

The retained default backend tests produce **7 passed, 1 failed, 89 deselected**, matching the pre-migration current-suite result: `test_distance_from_preferred_length_is_a_penalty` expects multiplier `1` while the current objective returns `-1`. Solver correction is subsequent work. Test discovery is now limited to `api/tests/`, preventing accidental collection of archived duplicate tests. Use `uv run python -m pytest` from `api/` so the non-installed application imports through normal module execution.

Frontend lint produces **0 errors and 12 existing warnings** before and after relocation. TypeScript and production builds stop at the same pre-existing `lowdb-employee.repository.ts` call to `db.write()` on a read-only employee API result. No errors are suppressed; employee write/removal behavior belongs to the employee feature slice. Next.js compilation succeeds before that type gate.

The API image builds on Linux arm64; its application lifespan, `/status` and Microsoft ODBC Driver 18 load check pass without database access. The native Next.js development home page returns HTTP 200, and its relative case directory resolves to the two imported case roots. The root MkDocs strict build passes with no warnings; historical footnote diagnostics remain informational. These checks do not establish live TimeOffice connectivity, accepted schedules or final Linux-host startup.
