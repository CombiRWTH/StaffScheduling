import json
import logging
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from src.loader import FSLoader
from src.solve import main as run_solver
from src.web.process_solution import process_solution

DEFAULT_WEIGHTS = {
    "free_weekend": 2,
    "consecutive_nights": 2,
    "hidden": 100,
    "overtime": 4,
    "consecutive_days": 1,
    "rotate": 1,
    "wishes": 3,
    "after_night": 3,
    "second_weekend": 1,
}

WEIGHTS_BALANCED = {
    "free_weekend": 5,
    "consecutive_nights": 1,
    "hidden": 50,
    "overtime": 10,
    "consecutive_days": 1,
    "rotate": 2,
    "wishes": 3,
    "after_night": 1,
    "second_weekend": 1,
}

WEIGHTS_STAFF_FOCUS = {
    "free_weekend": 0.1,
    "consecutive_nights": 5,
    "hidden": 80,
    "overtime": 1,
    "consecutive_days": 2,
    "rotate": 0,
    "wishes": 5,
    "after_night": 3,
    "second_weekend": 2,
}


def load_weights(unit: int, start_date: date) -> dict[str, Any]:
    """Loads weights from the JSON file or returns defaults if not found."""
    month_year = f"{start_date.month:02d}_{start_date.year}"
    weights_path = Path("cases") / str(unit) / month_year / "weights.json"

    if not weights_path.exists():
        logging.info("Weights file not found – using default weights instead.")
        return DEFAULT_WEIGHTS.copy()

    with weights_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def execute_solve(
    unit: int,
    start_date: date,
    end_date: date,
    timeout: int,
    weight_overrides: dict[str, int] | None = None,
    status_callback: Callable[[str], None] | None = None,
) -> str:
    """Executes a single solver run and processes the solution."""

    # 1. Load weights from JSON (or defaults) and apply any overrides
    weights = load_weights(unit, start_date)
    if weight_overrides:
        for key, value in weight_overrides.items():
            if key in weights:
                weights[key] = value
            else:
                raise ValueError(f"Unknown weight key '{key}'.")

    # 2. Run the solver
    result = run_solver(
        unit=unit,
        start_date=start_date,
        end_date=end_date,
        timeout=timeout,
        weights=weights,
        status_callback=status_callback,
    )

    # 3. Write the solution to files for the web frontend (only when a solution was found)
    if result.solution.status_name in ("FEASIBLE", "OPTIMAL"):
        loader = FSLoader(unit, start_date=start_date, end_date=end_date)
        solution_name = f"solution_{unit}_{start_date}-{end_date}_wdefault"

        process_solution(
            loader=loader,
            employees=result.employees,
            output_filename=solution_name + "_processed.json",
            solution_file_name=solution_name,
        )

    return result.solution.status_name


def execute_solve_multiple(
    unit: int,
    start_date: date,
    end_date: date,
    timeout: int,
    status_callback: Callable[[str, int, int], None] | None = None,
) -> list[str]:
    """Run the solver three times with different weight presets.

    Returns the list of status names produced by each run (in order).
    """
    employees = None
    statuses: list[str] = []
    weight_set = [DEFAULT_WEIGHTS, WEIGHTS_BALANCED, WEIGHTS_STAFF_FOCUS]
    for weight_id, weights in enumerate(weight_set):
        logging.info(
            f"Creating staff schedule for planning unit {unit} "
            f"from {start_date} to {end_date} with weight set {weight_id}"
        )

        # A small wrapper callback that bundles the phase (from solve.py)
        # and the current iteration (from that loop).
        def internal_phase_callback(phase_name: str, weight_id: int = weight_id) -> None:
            if status_callback is not None:
                status_callback(phase_name, weight_id, len(weight_set))

        result = run_solver(
            unit=unit,
            start_date=start_date,
            end_date=end_date,
            timeout=timeout,
            weights=weights,
            weight_id=weight_id,
            employees=employees,
            status_callback=internal_phase_callback,
        )

        # Important: We save the found employees for the next iteration,
        # so that phase 1 & 2 go faster!
        employees = result.employees
        statuses.append(result.solution.status_name)

        if result.solution.status_name in ("FEASIBLE", "OPTIMAL"):
            loader = FSLoader(unit, start_date=start_date, end_date=end_date)
            in_name = f"solution_{unit}_{start_date}-{end_date}_w{weight_id}"

            process_solution(
                loader=loader,
                employees=employees,
                output_filename=in_name + "_processed.json",
                solution_file_name=in_name,
            )

    return statuses
