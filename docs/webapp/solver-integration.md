# Integration limits

The webapp defaults to API mode. Next.js server-side callers use `SOLVER_API_URL` (default `http://127.0.0.1:8000`); start FastAPI separately from `api/`. See [installation](../installation.md) and the [API reference](../developer-view/api.md).

The relocated backend exposes `/status`, employee/configuration routes, `/solve/options`, `/solve/`, `/solve/jobs/{job_id}` and schedule routes. `/status` establishes process liveness only. The canonical solver runs one planning month with process-local jobs and one solve lock.

The imported frontend's old `/fetch`, `/insert`, `/delete`, multi-solve and progress-phase assumptions are not implemented by these backend routes. It expects `/schedules/metadata`, while `/schedules` currently returns an empty placeholder list. Its file-based case discovery and employee/configuration schemas also differ from the canonical API domain. These gaps require subsequent feature slices; relocation does not supply missing behavior.

`api/cases/` and `webapp/cases/` retain different historical inputs. API output is written below the API working directory, while the webapp reads its own case files. They are not a shared synchronized store. Frontend CLI mode remains legacy code, disabled by the safe template; the retained Python CLI supports only a full-month `solve` and is invoked with `uv run python -m app.cli`.

Historical progress phases, fixed weight presets, CLI commands and write-back descriptions are retained in the [historical integration reference](../collection-of-old-docs/webapp/solver-integration.md). They are not the contract of the canonical backend. Do not use the imported UI as evidence that a schedule is valid or has been safely published.
