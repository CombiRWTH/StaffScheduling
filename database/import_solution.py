import json
import ast
import pyodbc
import os
import re
import unicodedata
import pandas as pd
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
from pathlib import Path
from collections import Counter
from connection_setup import get_db_connection_string

# Load the .env-file for file import purposes
load_dotenv()


def load_json_files():
    """Load the needed Employee file and the corresponding solution file,
    which includes the shifts references to employees."""
    base_path = Path(__file__).parent.resolve()
    base_folder = os.getenv("BASE_OUTPUT_FOLDER")
    # sub_folder = os.getenv("SUB_OUTPUT_FOLDER")
    sub_folder = "2"

    solution_file = base_path / "solutions_test.json"
    employee_file = Path(base_folder) / sub_folder / "employees.json"

    with open(solution_file, encoding="utf-8") as f:
        data = json.load(f)
    with open(employee_file, encoding="utf-8") as f:
        emp_data = json.load(f)["employees"]
    return data, emp_data


def get_correct_path(filename):
    """Return the correct path to store the given file in."""
    # Get the defined folder names out of the .env-file
    base_folder = os.getenv("BASE_OUTPUT_FOLDER")
    sub_folder = os.getenv("SUB_OUTPUT_FOLDER")
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Create the output path to store the file in
    target_dir = os.path.join(current_dir, "..", base_folder, sub_folder)
    target_dir = os.path.abspath(target_dir)
    output_path = os.path.join(target_dir, filename)
    return output_path


# Helper functions
def norm(s: str) -> str:
    """Lower case, Unicode normalization, merge spaces"""
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def variants(last: str, first: str):
    """Generates common spellings of a name pair."""
    raw = [
        f"{last} {first}",
        f"{first} {last}",
        f"{last}, {first}",
        f"{first}, {last}",
    ]
    return [norm(x) for x in raw]


def load_person_to_job(conn_str: str) -> dict[int, int]:
    """Reads TPersonal (Prim, RefBerufe) and returns {Prim: RefBerufe}."""
    sql = "SELECT Prim, RefBerufe FROM TPersonal"
    with pyodbc.connect(conn_str) as cn:
        return {row.Prim: row.RefBerufe for row in cn.cursor().execute(sql)}


def load_shift_segments(
    conn_str: str, shift_id_map: dict[int, int]
) -> dict[int, list[tuple[time, time, int]]]:
    """Load the correct times for each shift type."""
    sql = """
        SELECT Kommt, Geht
        FROM   TDiensteSollzeiten
        WHERE  RefDienste = ?
        ORDER  BY Kommt
    """

    segments_by_shift = {}

    with pyodbc.connect(conn_str) as cn:
        cur = cn.cursor()
        for shift_id, ref_dienst in shift_id_map.items():
            cur.execute(sql, ref_dienst)
            rows = cur.fetchall()
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

    print(segments_by_shift)
    return segments_by_shift


def build_key2prim(emp_data):
    last_counts = Counter(norm(e["name"]) for e in emp_data)
    unique_last = {ln for ln, c in last_counts.items() if c == 1}

    key2prim = {}
    for emp in emp_data:
        ln, fn, prim = norm(emp["name"]), norm(emp["firstname"]), emp["Prim"]

        for v in variants(ln, fn):
            key2prim[v] = prim

        if ln in unique_last:
            key2prim[ln] = prim
    return key2prim


def map_indices_to_prims(data, key2prim):
    idx_to_name = data["employees"]["name_to_index"]
    idx_to_prim, unmatched = {}, []
    for full_name, idx in idx_to_name.items():
        key = norm(full_name)
        prim = key2prim.get(key)
        if prim is not None:
            idx_to_prim[idx] = prim
        else:
            unmatched.append(full_name)
    return idx_to_prim, unmatched


def build_dataframe(
    data,
    idx_to_prim,
    prim_to_refberuf,
    shift_segments,
    shift_to_refdienst,
    pe_id,
    plan_id,
    status_id,
):
    """Build the solution into one DataFrame (one row per segment)."""
    records = []
    for key, val in data["solutions"][0].items():
        if val != 1:
            continue

        emp_idx, date_str, shift_id = ast.literal_eval(key)
        base_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        ref_dienst = shift_to_refdienst[shift_id]
        prim_person = idx_to_prim[emp_idx]
        prim_beruf = prim_to_refberuf.get(prim_person)

        if prim_beruf is None:
            raise ValueError(f"Kein RefBerufe für Personal-Prim {prim_person}")

        for seg_idx, (von_t, bis_t, offset) in enumerate(
            shift_segments[shift_id], start=1
        ):
            datum = base_date + timedelta(days=offset)
            von_dt = datetime.combine(datum, von_t)
            bis_dt = datetime.combine(datum, bis_t)
            dauer_min = int((bis_dt - von_dt).total_seconds() // 60)

            records.append(
                {
                    "RefPlan": plan_id,
                    "RefPersonal": prim_person,
                    "Datum": datum,
                    "RefStati": status_id,
                    "lfdNr": 0,
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
    # lfdNr assigned per day/employee/status
    df["lfdNr"] = (
        df.sort_values(["RefPersonal", "Datum", "VonZeit"])
        .groupby(["RefPersonal", "Datum", "RefStati"])
        .cumcount()
        + 1
    )
    return df


def insert_dataframe_to_db(df, conn_str):
    """Insert the correctly formatted solution into the database."""
    with pyodbc.connect(conn_str) as conn:
        cursor = conn.cursor()
        cursor.fast_executemany = True

        insert_sql = """
            INSERT INTO TPlanPersonalKommtGeht
            (RefPlan, RefPersonal, Datum, RefStati, lfdNr,
            RefgAbw, RefDienste, RefBerufe, RefPlanungseinheiten,
            VonZeit, BisZeit, RefDienstAbw, Minuten, Info,
            RefEinsatzArten, Wunschdienst, BereitVon, BereitBis,
            RefDiensteSpezTypenElemente, RefPeinheitOwner,
            RefSeminareTermine, VBAHerkunft)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """

        params = [
            (
                row.RefPlan,
                row.RefPersonal,
                row.Datum,
                row.RefStati,
                row.lfdNr,
                row.RefgAbw,
                row.RefDienste,
                row.RefBerufe,
                row.RefPlanungseinheiten,
                row.VonZeit,
                row.BisZeit,
                row.RefDienstAbw,
                row.Minuten,
                row.Info,
                row.RefEinsatzArten,
                row.Wunschdienst,
                row.BereitVon,
                row.BereitBis,
                row.RefDiensteSpezTypenElemente,
                row.RefPeinheitOwner,
                row.RefSeminareTermine,
                row.VBAHerkunft,
            )
            for row in df.itertuples(index=False)
        ]

        cursor.executemany(insert_sql, params)
        conn.commit()

    print(f"{len(df):,} Lines inserted in TPlanPersonalKommtGeht.")


def run():
    conn_str = get_db_connection_string()
    data, emp_data = load_json_files()
    prim_to_refberuf = load_person_to_job(conn_str)
    key2prim = build_key2prim(emp_data)
    idx_to_prim, unmatched = map_indices_to_prims(data, key2prim)

    if unmatched:
        print("Not yet assigned:", ", ".join(unmatched))
    else:
        print("All names successfully mapped!")

    # Currently hardcoded at the "wrong" spot!
    PE_ID = 77
    PLAN_ID = 17193
    STATUS_ID = 20

    # Corresponding shift IDs to given counts of shifts
    SHIFT_TO_REFDIENST = {0: 2939, 1: 2947, 2: 2953, 3: 2906}
    # Shift mapping with format: shift_id : [ (von_time, bis_time, day_offset) , … ]
    SHIFT_SEGMENTS = load_shift_segments(conn_str, SHIFT_TO_REFDIENST)

    df = build_dataframe(
        data,
        idx_to_prim,
        prim_to_refberuf,
        SHIFT_SEGMENTS,
        SHIFT_TO_REFDIENST,
        PE_ID,
        PLAN_ID,
        STATUS_ID,
    )

    # When needed to write into the database directly:
    # insert_dataframe_to_db(df, conn_str)

    # Test export as a json file to check if the output is correct without actually writing into the db:
    test_file = df.to_dict(orient="records")
    output_json = {"test": test_file}

    filename = "test_file.json"

    # Store JSON-file within given directory
    json_output = json.dumps(output_json, ensure_ascii=False, indent=2, default=str)
    store_path = get_correct_path(filename)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    # Print a message of completed export
    print(f"✅ Export abgeschlossen – {filename} erstellt")


if __name__ == "__main__":
    run()
