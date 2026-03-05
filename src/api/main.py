import io
import logging
import sys
from contextlib import contextmanager
from datetime import date

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.db.export_main import main as fetcher
from src.db.import_main import main as inserter
from src.services.solve_service import execute_solve, execute_solve_multiple

load_dotenv()
app = FastAPI(title="Staff Scheduling API")

# Global state tracking the current solver phase.
# Shared between the /status endpoint and the /solve endpoint.
solver_state: dict[str, bool | str | int] = {
    "is_solving": False,
    "phase": "idle",
    "timeout_set_for_phase_3": 0,
}

# ---------------------------------------------------------------------------
# Utility context manager to capture stdout (for debugging purposes)
# ---------------------------------------------------------------------------


class TeeStream:
    """Writes in parallel to the real stdout (console) and to our string buffer (API)."""

    def __init__(self, original_stream, capture_buffer):
        self.original_stream = original_stream
        self.capture_buffer = capture_buffer

    def write(self, data):
        self.original_stream.write(data)  # Print it to the console
        self.capture_buffer.write(data)  # Save it for the API response

    def flush(self):
        self.original_stream.flush()
        self.capture_buffer.flush()


@contextmanager
def capture_console_output():
    """Captures prints and logs for the API, while still outputting them to the console."""

    # 1. Branch the print output (Tee)
    stdout_capture = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = TeeStream(old_stdout, stdout_capture)

    # 2. Branch the logging output
    log_capture = io.StringIO()

    # We add a SECOND handler instead of replacing the existing one (which logs to the console).
    api_log_handler = logging.StreamHandler(log_capture)
    api_log_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    root_logger = logging.getLogger()
    root_logger.addHandler(api_log_handler)

    try:
        yield stdout_capture, log_capture
    finally:
        # Restore everything back to its normal state
        sys.stdout = old_stdout
        root_logger.removeHandler(api_log_handler)


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


class SolveMultipleRequest(SolveRequest):
    """Same as :class:`SolveRequest` but used for the
    ``/solve-multiple`` route for clarity.
    """


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/status")
def get_status() -> dict[str, bool | str | int]:
    """Return the current solver state."""
    return solver_state


@app.post("/fetch")
def fetch(request: DBRequest) -> dict[str, bool | str]:
    """Export planning data from the TimeOffice database to local JSON files."""
    with capture_console_output() as (stdout, logs):
        try:
            fetcher(request.planning_unit, request.from_date, request.till_date)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"success": True, "log": logs.getvalue(), "stdout": stdout.getvalue()}


@app.post("/insert")
def insert(request: DBRequest) -> dict[str, bool | str]:
    """Insert a previously generated solution into the TimeOffice database."""
    with capture_console_output() as (stdout, logs):
        try:
            inserter(request.planning_unit, request.from_date, request.till_date, cli_input="i")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"success": True, "log": logs.getvalue(), "stdout": stdout.getvalue()}


@app.post("/delete")
def delete(request: DBRequest) -> dict[str, bool | str]:
    """Delete a previously inserted solution from the TimeOffice database."""
    with capture_console_output() as (stdout, logs):
        try:
            inserter(request.planning_unit, request.from_date, request.till_date, cli_input="d")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"success": True, "log": logs.getvalue(), "stdout": stdout.getvalue()}


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
    with capture_console_output() as (stdout, logs):
        try:
            result_status = execute_solve(
                unit=request.unit,
                start_date=request.start_date,
                end_date=request.end_date,
                timeout=request.timeout,
                status_callback=phase_callback,
            )
            success = result_status in ("FEASIBLE", "OPTIMAL")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            solver_state["is_solving"] = False
            solver_state["phase"] = "idle"
            solver_state["timeout_set_for_phase_3"] = 0
    log_output = logs.getvalue()
    stdout_output = stdout.getvalue()

    return {"success": success, "status": result_status, "log": log_output, "stdout": stdout_output}


@app.post("/solve-multiple")
def solve_multiple(request: SolveMultipleRequest) -> dict[str, bool | list[str] | str]:
    """
    Run three solver iterations with different weight configurations.

    The solver state is updated with ``phase`` ``weight_id``, ``total_weights`` so
    the frontend can show which iteration is currently running.
    Returns ``{"success": True/False, "status": "COMPLETED"}``.
    """
    solver_state["is_solving"] = True
    solver_state["timeout_set_for_phase_3"] = request.timeout
    solver_state["weight_id"] = 0
    solver_state["total_weights"] = 0

    def phase_callback(phase_name: str, weight_id: int, total_weights: int) -> None:
        solver_state["phase"] = phase_name
        solver_state["weight_id"] = weight_id
        solver_state["total_weights"] = total_weights

    result_status = []  # Collect statuses from all iterations
    success = False
    with capture_console_output() as (stdout, logs):
        try:
            # execute_solve_multiple returns a list of status names
            statuses = execute_solve_multiple(
                unit=request.unit,
                start_date=request.start_date,
                end_date=request.end_date,
                timeout=request.timeout,
                status_callback=phase_callback,
            )
            # success if at least one run produced a feasible/optimal result
            success = any(s in ("FEASIBLE", "OPTIMAL") for s in statuses)
            result_status = statuses
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            solver_state["is_solving"] = False
            solver_state["phase"] = "idle"
            solver_state["timeout_set_for_phase_3"] = 0
            solver_state["weight_id"] = 0
            solver_state["total_weights"] = 0

    return {"success": success, "statuses": result_status, "log": logs.getvalue(), "stdout": stdout.getvalue()}


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
