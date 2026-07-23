import json
import logging
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

PROCESSED_SOLUTIONS_DIR = Path("processed_solutions")

schedule_router = APIRouter()

# ── Metadata ─────────────────────────────────────────────────────────


@schedule_router.get("/schedules/metadata")
async def get_schedules_metadata(planning_unit: int, from_date: date) -> Any:
    """Return schedule metadata for a planning unit and month."""
    return _get_metadata_legacy(planning_unit=planning_unit, from_date=from_date)


@schedule_router.put("/schedules/metadata")
async def put_schedules_metadata(planning_unit: int, from_date: date, request: dict[str, Any]) -> dict[str, bool]:
    """Write schedule metadata for a planning unit and month."""
    _put_metadata_legacy(request["data"])
    return {"success": True}


@schedule_router.get("/schedules/last-inserted")
async def get_last_inserted_schedule(planning_unit: int, from_date: date) -> Any:
    """Return the last inserted schedule marker for a planning unit and month."""
    return _get_last_inserted_legacy()


@schedule_router.put("/schedules/last-inserted")
async def put_last_inserted_schedule(planning_unit: int, from_date: date, request: dict[str, Any]) -> dict[str, bool]:
    """Write the last inserted schedule marker for a planning unit and month."""
    _put_last_inserted_legacy(request["data"])
    return {"success": True}


@schedule_router.delete("/schedules/last-inserted")
async def delete_last_inserted_schedule(planning_unit: int, from_date: date) -> dict[str, bool]:
    """Delete the last inserted schedule marker for a planning unit and month."""
    _delete_last_inserted_legacy()
    return {"success": True}


# ── Schedule solutions ───────────────────────────────────────────────


@schedule_router.get("/schedules/{schedule_id}")
async def get_schedule(
    planning_unit: int,
    from_date: date,
    schedule_id: str,
) -> Any:
    """Return a schedule solution for a planning unit and month."""
    return _get_solution_legacy(schedule_id, planning_unit=planning_unit, from_date=from_date)


@schedule_router.put("/schedules/{schedule_id}")
async def put_schedule(
    planning_unit: int, from_date: date, schedule_id: str, request: dict[str, Any]
) -> dict[str, bool]:
    """Write a schedule solution for a planning unit and month."""
    _put_solution_legacy(schedule_id, request["data"])
    return {"success": True}


@schedule_router.delete("/schedules/{schedule_id}")
async def delete_schedule(planning_unit: int, from_date: date, schedule_id: str) -> dict[str, bool]:
    """Delete a schedule solution for a planning unit and month."""
    _delete_solution_legacy(schedule_id)
    return {"success": True}


# ── Legacy file helper functions (TODO: replace with database calls) ─────


def _get_metadata_legacy(planning_unit: int | None = None, from_date: date | None = None) -> Any:
    """Read schedule metadata from the legacy JSON file or dynamically discover processed solutions."""
    metadata_path = PROCESSED_SOLUTIONS_DIR / "schedules.json"

    if metadata_path.is_file():
        try:
            with metadata_path.open(encoding="utf-8") as f:
                data = json.load(f)
                if data.get("schedules"):
                    return data
        except json.JSONDecodeError as exc:
            logger.warning("Schedules metadata file is invalid JSON, falling back to discovery: %s", exc)

    if not PROCESSED_SOLUTIONS_DIR.is_dir():
        return {"schedules": [], "selectedScheduleId": None}

    # Dynamically discover solutions in processed_solutions
    schedules: list[dict[str, Any]] = []
    unit_prefix = f"solution_{planning_unit}_" if planning_unit is not None else "solution_"

    matching_files = sorted(
        [
            p
            for p in PROCESSED_SOLUTIONS_DIR.glob("*.json")
            if p.name != "schedules.json"
            and p.name != "last_inserted.json"
            and (planning_unit is None or unit_prefix in p.name or f"_{planning_unit}_" in p.name)
        ],
        key=lambda p: p.stat().st_mtime,
    )

    for path in matching_files:
        schedule_id = path.name
        if schedule_id.endswith("_processed.json"):
            schedule_id = schedule_id[:-15]
        elif schedule_id.endswith(".json"):
            schedule_id = schedule_id[:-5]

        stats = {}
        try:
            with path.open(encoding="utf-8") as f:
                file_data = json.load(f)
                inner = file_data.get("solution", file_data) if isinstance(file_data, dict) else {}
                if isinstance(inner, dict):
                    stats = inner.get("stats", {})
        except Exception:
            pass

        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat()
        schedules.append(
            {
                "scheduleId": schedule_id,
                "description": f"Solver-generiert: {schedule_id}",
                "generatedAt": mtime,
                "isSelected": False,
                "stats": stats,
            }
        )

    selected_id = None
    if schedules:
        schedules[-1]["isSelected"] = True
        selected_id = schedules[-1]["scheduleId"]

    return {"schedules": schedules, "selectedScheduleId": selected_id}


def _put_metadata_legacy(data: Any) -> None:
    """Write schedule metadata to the legacy JSON file, placeholder until database read/write."""
    metadata_path = PROCESSED_SOLUTIONS_DIR / "schedules.json"

    try:
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with metadata_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not write schedules metadata file: {metadata_path}",
        ) from exc


def _get_last_inserted_legacy() -> Any:
    """Read the last-inserted marker from the legacy JSON file, placeholder until database read/write."""
    last_inserted_path = PROCESSED_SOLUTIONS_DIR / "last_inserted.json"

    if not last_inserted_path.is_file():
        return None

    try:
        with last_inserted_path.open(encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Last inserted schedule file is invalid JSON: {last_inserted_path}",
        ) from exc


def _put_last_inserted_legacy(data: Any) -> None:
    """Write the last-inserted marker to the legacy JSON file, placeholder until database read/write."""
    last_inserted_path = PROCESSED_SOLUTIONS_DIR / "last_inserted.json"

    try:
        last_inserted_path.parent.mkdir(parents=True, exist_ok=True)
        with last_inserted_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not write last inserted schedule file: {last_inserted_path}",
        ) from exc


def _delete_last_inserted_legacy() -> None:
    """Delete the last-inserted marker legacy JSON file, placeholder until database read/write."""
    last_inserted_path = PROCESSED_SOLUTIONS_DIR / "last_inserted.json"

    try:
        last_inserted_path.unlink()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Last inserted schedule file not found: {last_inserted_path}",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not delete last inserted schedule file: {last_inserted_path}",
        ) from exc


def _get_solution_legacy(schedule_id: str, planning_unit: int | None = None, from_date: date | None = None) -> Any:
    """Read a processed solution from the legacy JSON files, placeholder until database read/write."""
    candidate_paths = [
        PROCESSED_SOLUTIONS_DIR / f"{schedule_id}_processed.json",
        PROCESSED_SOLUTIONS_DIR / f"{schedule_id}.json",
    ]

    if schedule_id.endswith("_processed"):
        base_id = schedule_id[:-10]
        candidate_paths.append(PROCESSED_SOLUTIONS_DIR / f"{base_id}_processed.json")
        candidate_paths.append(PROCESSED_SOLUTIONS_DIR / f"{base_id}.json")

    solution_path = None
    for p in candidate_paths:
        if p.is_file():
            solution_path = p
            break

    # Fallback search by planning_unit if exact file not found
    if solution_path is None and planning_unit is not None and PROCESSED_SOLUTIONS_DIR.is_dir():
        unit_prefix = f"solution_{planning_unit}_"
        matches = sorted(
            [
                p
                for p in PROCESSED_SOLUTIONS_DIR.glob("*.json")
                if p.name != "schedules.json"
                and p.name != "last_inserted.json"
                and (unit_prefix in p.name or f"_{planning_unit}_" in p.name)
            ],
            key=lambda p: p.stat().st_mtime,
        )
        if matches:
            solution_path = matches[-1]

    if solution_path is None or not solution_path.is_file():
        return {"solution": None}

    with solution_path.open(encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "solution" in data:
        return data
    else:
        return {"solution": data}


def _put_solution_legacy(schedule_id: str, data: Any) -> None:
    """Write a processed solution to the legacy JSON file, placeholder until database read/write."""
    schedule_path = PROCESSED_SOLUTIONS_DIR / f"{schedule_id}_processed.json"

    try:
        schedule_path.parent.mkdir(parents=True, exist_ok=True)
        with schedule_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not write schedule file: {schedule_path}",
        ) from exc


def _delete_solution_legacy(schedule_id: str) -> None:
    """Delete a processed solution legacy JSON file, placeholder until database read/write."""
    schedule_path = PROCESSED_SOLUTIONS_DIR / f"{schedule_id}_processed.json"

    try:
        schedule_path.unlink()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule file not found: {schedule_path}",
        ) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Could not delete schedule file: {schedule_path}",
        ) from exc
