import json
import ast
import os
import pandas as pd
import logging
from datetime import datetime, time, timedelta
from sqlalchemy import text


logging.basicConfig(level=logging.INFO)


def get_correct_path(filename, planning_unit):
    """Return the correct path to store the given file in."""

    # Get the defined folder names out of the .env-file
    base_folder = os.getenv("BASE_OUTPUT_FOLDER")

    # Create the output path to store the file in
    target_dir = os.path.join("./", base_folder, str(planning_unit))
    target_dir = os.path.abspath(target_dir)
    output_path = os.path.join(target_dir, filename)
    return output_path


def load_json_files(start_date, end_date, planning_unit):
    """Load the needed Employee file and the corresponding solution file,
    which includes the shifts references to employees."""
    sol_folder = "found_solutions"

    solution_dir = os.path.join("./", sol_folder)
    solution_file = os.path.join(
        solution_dir, f"solution_{planning_unit}_{start_date}-{end_date}.json"
    )

    employee_file = get_correct_path("employees.json", planning_unit)

    with open(solution_file, encoding="utf-8") as f:
        data = json.load(f)
    with open(employee_file, encoding="utf-8") as f:
        emp_data = json.load(f)["employees"]
    return data, emp_data


def load_planned_shifts(planning_unit) -> dict[int, set[int]]:
    """
    Returns Dict {Key : {Day1, Day2, …}},
    based on planned_shifts in free_shifts_and_vacation_days.json.
    """

    file_path = get_correct_path("free_shifts_and_vacation_days.json", planning_unit)
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)["employees"]

    prim2days = {}
    for emp in data:
        days = {d for d, _ in emp.get("planned_shifts", [])}
        prim2days[int(emp["key"])] = days
    return prim2days


def load_person_to_job(engine) -> dict[int, int]:
    """Reads TPersonal (Prim, RefBerufe) and returns {Prim: RefBerufe}."""
    sql = text("SELECT Prim, RefBerufe FROM TPersonal")
    with engine.connect() as connection:
        result = connection.execute(sql)
        return {row.Prim: row.RefBerufe for row in result}


def load_shift_segments(
    engine, shift_id_map: dict[int, int]
) -> dict[int, list[tuple[time, time, int]]]:
    """Load the correct times for each shift type."""
    sql = text("""
        SELECT Kommt, Geht
        FROM   TDiensteSollzeiten
        WHERE  RefDienste = :ref
        ORDER  BY Kommt
    """)

    segments_by_shift = {}

    with engine.connect() as conn:
        for shift_id, ref_dienst in shift_id_map.items():
            if shift_id > 4:
                continue

            rows = conn.execute(sql, {"ref": ref_dienst}).fetchall()
            if not rows:
                raise ValueError(
                    f"TDiensteSollzeiten does not contain an entry for RefDienste {ref_dienst}"
                )

            base_date = rows[0].Kommt.date()
            segments = []

            for r in rows:
                offset = (r.Kommt.date() - base_date).days
                segments.append((r.Kommt.time(), r.Geht.time(), offset))

            segments_by_shift[shift_id] = segments

    return segments_by_shift


def build_dataframe(
    data,
    emp_data,
    prim_to_refberuf,
    shift_segments,
    shift_to_refdienst,
    pe_id,
    plan_id,
    status_id,
    planned_map,
):
    """Build the solution into one DataFrame (one row per segment)."""

    prim_whitelist = {int(e["key"]) for e in emp_data}

    records = []
    for key, val in data["variables"].items():
        if val != 1:
            continue

        try:
            prim_person, date_str, shift_id = ast.literal_eval(key)
        except (ValueError, SyntaxError):
            # f.e. ignore "e:459_d:2024-11-01"
            continue

        # Filter for unknown shift ids (f.e. from other PEs)
        if shift_id not in shift_to_refdienst:
            continue

        # Filter for unknown employees (f.e. ghost employees)
        if prim_person not in prim_whitelist:
            continue

        base_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Filter for already planned shifts (shifts already in DB)
        planned_days = planned_map.get(prim_person, set())
        if base_date.day in planned_days:
            continue

        ref_dienst = shift_to_refdienst[shift_id]
        prim_beruf = prim_to_refberuf.get(prim_person)

        if prim_beruf is None:
            raise ValueError(f"Kein RefBerufe für Personal-Prim {prim_person}")

        for seg_idx, (von_t, bis_t, offset) in enumerate(
            shift_segments[shift_id], start=1
        ):
            datum = base_date
            vonbis_tag = base_date + timedelta(days=offset)
            von_dt = datetime.combine(vonbis_tag, von_t)
            bis_dt = datetime.combine(vonbis_tag, bis_t)
            dauer_min = int((bis_dt - von_dt).total_seconds() // 60)

            records.append(
                {
                    "RefPlan": plan_id,
                    "RefPersonal": prim_person,
                    "Datum": datum,
                    "RefStati": status_id,
                    "lfdNr": seg_idx,
                    "RefgAbw": None,
                    "RefDienste": ref_dienst,
                    "RefBerufe": prim_beruf,
                    "RefPlanungseinheiten": pe_id,
                    "VonZeit": von_dt,
                    "BisZeit": bis_dt,
                    "RefDienstAbw": None,
                    "Minuten": dauer_min,
                    "Info": None,
                    "RefEinsatzArten": None,
                    "Wunschdienst": None,
                    "BereitVon": None,
                    "BereitBis": None,
                    "RefDiensteSpezTypenElemente": None,
                    "RefPeinheitOwner": pe_id,
                    "RefSeminareTermine": None,
                    "VBAHerkunft": None,
                }
            )

    df = pd.DataFrame(records)
    return df


def insert_dataframe_to_db(df, engine):
    """Insert the correctly formatted solution into the database."""

    insert_sql = text("""
        INSERT INTO TPlanPersonalKommtGeht
        (RefPlan, RefPersonal, Datum, RefStati, lfdNr,
        RefgAbw, RefDienste, RefBerufe, RefPlanungseinheiten,
        VonZeit, BisZeit, RefDienstAbw, Minuten, Info,
        RefEinsatzArten, Wunschdienst, BereitVon, BereitBis,
        RefDiensteSpezTypenElemente, RefPeinheitOwner,
        RefSeminareTermine, VBAHerkunft)
        VALUES (
            :RefPlan, :RefPersonal, :Datum, :RefStati, :lfdNr,
            :RefgAbw, :RefDienste, :RefBerufe, :RefPlanungseinheiten,
            :VonZeit, :BisZeit, :RefDienstAbw, :Minuten, :Info,
            :RefEinsatzArten, :Wunschdienst, :BereitVon, :BereitBis,
            :RefDiensteSpezTypenElemente, :RefPeinheitOwner,
            :RefSeminareTermine, :VBAHerkunft
        )
    """)

    params = df.to_dict(orient="records")

    with engine.begin() as conn:
        conn.execution_options(fast_executemany=True)
        conn.execute(insert_sql, params)

    logging.info(f"{len(df):,} Lines inserted in TPlanPersonalKommtGeht.")


def delete_dataframe_from_db(df, engine):
    """Delete the solution in the dataframe from the database."""

    delete_sql = text("""
        DELETE FROM TPlanPersonalKommtGeht
        WHERE RefPlan       = :RefPlan
        AND RefPersonal     = :RefPersonal
        AND Datum           = :Datum
        AND lfdNr           = :lfdNr
        AND RefDienste      = :RefDienste
    """)

    keys = df[["RefPlan", "RefPersonal", "Datum", "lfdNr", "RefDienste"]]
    params = keys.to_dict(orient="records")

    with engine.begin() as conn:
        conn.execution_options(fast_executemany=True)
        conn.execute(delete_sql, params)

    logging.info(f"{len(df):,} Lines deleted in TPlanPersonalKommtGeht.")
