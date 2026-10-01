# Integration limits

The webapp defaults to API mode. Next.js server-side callers use `SOLVER_API_URL` (default `http://127.0.0.1:8000`); start FastAPI separately from `api/`. See [installation](../installation.md) and the [API reference](../developer-view/api.md).

The relocated backend exposes `/status`, employee/configuration routes, `/solve/options`, `/solve/`, `/solve/jobs/{job_id}` and schedule routes. `/status` establishes process liveness only. The canonical solver runs one planning month with process-local jobs and one solve lock.

The imported frontend's old `/fetch`, `/insert`, `/delete`, multi-solve and progress-phase assumptions are not implemented by these backend routes. It expects `/schedules/metadata`, while `/schedules` currently returns an empty placeholder list. Its file-based case discovery and employee/configuration schemas also differ from the canonical API domain. These gaps require subsequent feature slices; relocation does not supply missing behavior.

Historical service case directories and both CLI launchers have been removed. The API is the only solver entry point. Existing file-based screens retain their behavior until their canonical feature replacements; runtime files belong under root `data/`. This does not create a synchronized canonical planning store.

Historical progress phases, fixed weight presets, CLI commands and write-back descriptions are retained in the [historical integration reference](../collection-of-old-docs/webapp/solver-integration.md). They are not the contract of the canonical backend. Do not use the imported UI as evidence that a schedule is valid or has been safely published.
