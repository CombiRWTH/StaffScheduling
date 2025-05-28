"""Second phase: add intermediate (Z) shifts after an initial schedule has been
created by the first-phase CP-SAT model.

Das Modul fügt die FEWEST möglichen Z-Schichten ein, sodass jede*r Beschäftigte
mindestens `target_minutes − tolerance` Minuten erreicht – unter Einhaltung
aller Geschäftsregeln.

Neue Zielfunktion
-----------------
1. Minimiere das Maximum der Z-Schichten, die an einem einzelnen Tag vorkommen.
2. Wenn mehrere Pläne dasselbe Maximum haben, minimiere die Gesamtzahl aller Z.

Debug-Ausgaben zeigen pro Mitarbeiter:
* Defizit in Minuten
* Anzahl der möglichen Z-Slots
* Warnung, falls keine Slots verfügbar sind
"""

from __future__ import annotations

import json
from math import ceil
from pathlib import Path
from typing import List

from ortools.sat.python import cp_model


# ──────────────────── Helper: Daten aus JSON laden ──────────────────────────
def _load_target_minutes_json(case_id: int):
    """Return (target_minutes, tolerance, shift_duration_by_index)."""
    fname = Path(f"./cases/{case_id}/target_working_minutes.json")
    if not fname.exists():
        raise FileNotFoundError(fname)

    data = json.loads(fname.read_text(encoding="utf-8"))

    # --- Ziel-Minuten pro Mitarbeiter --------------------------------------
    if "employees" in data:  # neues Format
        target_block = {emp["name"]: int(emp["target"]) for emp in data["employees"]}
    else:  # Legacy-Keys
        target_block = (
            data.get("target_minutes")
            or data.get("target_working_minutes")
            or data.get("target_hours")
        )
        if target_block is None:
            raise KeyError("No target minutes found in JSON file.")

    def h2min(x):
        return int(x * 60) if isinstance(x, (int, float)) and x < 1000 else int(x)

    target_minutes = (
        {k: h2min(v) for k, v in target_block.items()}
        if isinstance(target_block, dict)
        else h2min(target_block)
    )

    # --- Toleranz -----------------------------------------------------------
    tolerance = (
        data.get("tolerance_minutes")
        or max(data.get("tolerance_less", 0), data.get("tolerance_more", 0))
        or 460
    )

    # --- Schichtdauern ------------------------------------------------------
    shift_durations = {
        **{"F": 460, "S": 460, "N": 720, "Z": 460},
        **data.get("shift_durations", {}),
    }
    sym_to_idx = {"F": 0, "S": 1, "N": 2, "Z": 3}
    shift_dur_idx = {
        sym_to_idx[k]: v for k, v in shift_durations.items() if k in sym_to_idx
    }

    return target_minutes, tolerance, shift_dur_idx


# ──────────────────── Haupt-Routine Phase 2 ─────────────────────────────────
def add_intermediate_shifts_to_solutions(
    solutions: List[dict],
    employees: List[dict],
    dates: List,  # list[datetime.date]
    case_id: int,
) -> List[dict]:
    """Insert Z-shifts where needed, minimise max per day, print debug info."""
    target_raw, tolerance, shift_dur = _load_target_minutes_json(case_id)
    z_duration = shift_dur[3]

    # name_to_idx = {emp["name"]: idx for idx, emp in enumerate(employees)}
    idx_to_name = {idx: emp["name"] for idx, emp in enumerate(employees)}

    num_employees = len(employees)
    num_days = len(dates)
    weekday_of = [d.weekday() for d in dates]  # 0=Mo … 6=So

    # Ziel-Minuten als Dict index → Minuten
    if isinstance(target_raw, dict):
        default_target = next(iter(target_raw.values()))
        target_by_idx = {
            idx: target_raw.get(emp["name"], default_target)
            for idx, emp in enumerate(employees)
        }
    else:
        target_by_idx = {idx: target_raw for idx in range(num_employees)}

    new_solutions: List[dict] = []
    total_z_added = 0

    # ───────────────── Lösungen iterieren ───────────────────────────────────
    for sol in solutions:
        worked_min = [0] * num_employees
        shift_on_day = [[None] * num_days for _ in range(num_employees)]

        # vorhandene Schichten einsammeln
        for (n, date_iso, s), v in sol.items():
            if v:
                d_idx = next(
                    i for i, dt in enumerate(dates) if dt.isoformat() == date_iso
                )
                shift_on_day[n][d_idx] = s
                worked_min[n] += shift_dur.get(s, 0)

        # -------- CP-SAT Modell Phase 2 -------------------------------------
        model = cp_model.CpModel()
        z_vars = {}

        for n in range(num_employees):
            for d in range(num_days):
                # Filter für zulässige Z-Slots
                if weekday_of[d] >= 5:  # Wochenende blockiert
                    continue
                if shift_on_day[n][d] is not None:  # Tag schon belegt
                    continue
                if d > 0 and shift_on_day[n][d - 1] == 2:  # Tag nach Nacht
                    continue
                # if d > 0 and shift_on_day[n][d - 1] in (0, 2):  # E→Z / N→Z
                #    continue
                # if d + 1 < num_days and shift_on_day[n][d + 1] in (0, 1, 2):  # Z→E/L/N
                #    continue

                z_vars[(n, d)] = model.NewBoolVar(f"z_{n}_{d}")

        # ----- Defizite + Constraints + Debug -------------------------------
        for n in range(num_employees):
            deficit = max(0, (target_by_idx[n] - tolerance) - worked_min[n])
            if deficit == 0:
                continue

            slots = [var for (emp, _), var in z_vars.items() if emp == n]
            slot_count = len(slots)
            need = ceil(deficit / z_duration)

            if slot_count == 0:
                print(f"⚠️  {idx_to_name[n]} deficit {deficit} min • 0 Z-Slots")
            else:
                print(
                    f"{idx_to_name[n]} deficit {deficit} min • Slots {slot_count} • need ≥ {need}"
                )
                model.Add(sum(slots) >= need)

        # ----- Zielfunktion: min max-daily-Z, dann Summe ---------------------
        if not z_vars:
            new_solutions.append(sol)
            continue

        daily_z = [
            model.NewIntVar(0, num_employees, f"dayZ_{d}") for d in range(num_days)
        ]
        for d in range(num_days):
            vars_today = [var for (emp, day), var in z_vars.items() if day == d]
            model.Add(daily_z[d] == sum(vars_today) if vars_today else 0)

        max_daily_z = model.NewIntVar(0, num_employees, "maxDailyZ")
        for d in range(num_days):
            model.Add(max_daily_z >= daily_z[d])

        BIG_M = num_employees * 100  # lexicographische Priorität
        model.Minimize(max_daily_z * BIG_M + sum(z_vars.values()))

        # ----- Lösen ---------------------------------------------------------
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("Phase 2: infeasible – behalte Ursprungsplan.")
            new_solutions.append(sol)
            continue

        # ----- Ergebnis mergen ----------------------------------------------
        merged = sol.copy()
        for (n, d), var in z_vars.items():
            if solver.BooleanValue(var):
                merged[(n, dates[d].isoformat(), 3)] = 1
                total_z_added += 1
        new_solutions.append(merged)

    print(f"Phase 2: added {total_z_added} Z-shifts across all solutions.")
    return new_solutions
