from datetime import date

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.db.export_main import main as fetcher
from src.db.import_main import main as inserter
from src.solve import main as run_solver

app = FastAPI(title="Staff Scheduling API")

# Global state tracking the current solver phase.
# Shared between the /status endpoint and the /solve endpoint.
solver_state: dict[str, bool | str | int] = {
    "is_solving": False,
    "phase": "idle",
    "timeout_set_for_phase_3": 0,
}


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class DBRequest(BaseModel):
    planning_unit: int
    from_date: date
    till_date: date


class SolveRequest(BaseModel):
    unit: int
    start_date: date
    end_date: date
    timeout: int = 300


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/status")
def get_status() -> dict[str, bool | str | int]:
    """Return the current solver state."""
    return solver_state


@app.post("/fetch")
def fetch(request: DBRequest) -> dict[str, bool]:
    """Export planning data from the TimeOffice database to local JSON files."""
    try:
        fetcher(request.planning_unit, request.from_date, request.till_date)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"success": True}


@app.post("/insert")
def insert(request: DBRequest) -> dict[str, bool]:
    """Insert a previously generated solution into the TimeOffice database."""
    try:
        inserter(request.planning_unit, request.from_date, request.till_date, cli_input="i")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"success": True}


@app.post("/delete")
def delete(request: DBRequest) -> dict[str, bool]:
    """Delete a previously inserted solution from the TimeOffice database."""
    try:
        inserter(request.planning_unit, request.from_date, request.till_date, cli_input="d")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"success": True}


@app.post("/solve")
def solve(request: SolveRequest) -> dict[str, bool | str]:
    """
    Run the staff scheduling solver.

    Updates ``solver_state["phase"]`` during execution so the frontend can
    display an accurate progress bar via ``GET /status``.
    Returns ``{"success": True/False, "status": "<OR-Tools status name>"}``.
    """
    solver_state["is_solving"] = True
    solver_state["timeout_set_for_phase_3"] = request.timeout

    def phase_callback(phase_name: str) -> None:
        solver_state["phase"] = phase_name

    result_status = "UNKNOWN"
    success = False
    try:
        result = run_solver(
            unit=request.unit,
            start_date=request.start_date,
            end_date=request.end_date,
            timeout=request.timeout,
            status_callback=phase_callback,
        )
        result_status = result.solution.status_name
        success = result_status in ("FEASIBLE", "OPTIMAL")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        solver_state["is_solving"] = False
        solver_state["phase"] = "idle"
        solver_state["timeout_set_for_phase_3"] = 0

    return {"success": success, "status": result_status}


# ---------------------------------------------------------------------------
# Entrypoint helpers
# ---------------------------------------------------------------------------


def main(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run the FastAPI application using uvicorn.

    This function exists so the application can be exposed via a console
    script or called from the project CLI.  ``uv run staff-scheduling-api``
    will execute this entry point when the package is installed.
    """
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
