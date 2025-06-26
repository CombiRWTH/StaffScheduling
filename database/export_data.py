import pandas as pd
import json
import os


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


def export_personal_data_to_json(engine, filename="employees.json"):
    """Export all personal staff information found within TPersonal and create a JSON-file."""
    # Write SQL-query to retrieve personal data
    query = """SELECT
                    a."Prim",
                    a."Name",
                    a."Vorname",
                    a."PersNr",
                    t."Bezeichnung" AS "Beruf"
                FROM "TPlanPersonal" b
                JOIN
                    "TPersonal" a ON b."RefPersonal" = a."Prim"
                LEFT JOIN
                    "TBerufe" t ON a."RefBerufe" = t."Prim"
                WHERE "RefPlan"=17193
            """
    df = pd.read_sql(query, engine)
    df = df.drop_duplicates()

    # Restructure and rename to the desired JSON-output-format
    df_renamed = df.rename(
        columns={
            "PersNr": "PersNr",
            "Vorname": "firstname",
            "Name": "name",
            "Beruf": "type",
        }
    )
    employees_list = df_renamed.to_dict(orient="records")
    output_json = {"employees": employees_list}

    # Store JSON-file within given directory
    json_output = json.dumps(output_json, ensure_ascii=False, indent=2)
    store_path = get_correct_path(filename)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    # Print a message of completed export
    print(f"✅ Export abgeschlossen – {filename} erstellt")


def export_target_working_minutes_to_json(
    engine, filename="target_working_minutes.json"
):
    """Export all target working minutes found within TPersonalKontenJeMonat and create a JSON-file."""
    # SQL Query to export the target working hours from TPersonalKontenJeMonat
    query = """SELECT
                    p.PersNr,
                    p.Name AS 'name',
                    p.Vorname AS 'firstname',
                    pkt.RefKonten,
                    pkt.Wert2
                FROM TPersonalKontenJeMonat pkt
                JOIN TPersonal p ON pkt.RefPersonal = p.Prim
                WHERE (pkt.RefKonten = 1  OR pkt.RefKonten = 19 OR pkt.RefKonten = 55) AND pkt.Monat = '202411' ORDER BY p.Name asc"""

    df = pd.read_sql(query, engine)

    # Converting hours to minutes
    df["Wert2"] = (df["Wert2"] * 60).round(0)

    # Merging different entries for each employee to summarize all Konten in one entry
    df_wide = (
        df.pivot_table(
            index=["PersNr", "name", "firstname"],
            columns="RefKonten",
            values="Wert2",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
        .rename(
            columns=lambda c: f"Wert_RefKonten{c}" if isinstance(c, (int, float)) else c
        )
    )

    # Choosing right Konto (see DatabaseQueries.md)
    df_wide["Wert_RefKonten19_55"] = df_wide[
        ["Wert_RefKonten19", "Wert_RefKonten55"]
    ].max(axis=1)

    #
    df_wide = df_wide.drop(columns=["Wert_RefKonten19", "Wert_RefKonten55"])

    # Renaming Columns
    df_wide = df_wide.rename(
        columns={"Wert_RefKonten1": "target", "Wert_RefKonten19_55": "actual"}
    )

    target_working_minutes_list = df_wide.to_dict(orient="records")
    output_json = {"target_working_minutes": target_working_minutes_list}

    # Store JSON-file within given directory
    json_output = json.dumps(output_json, ensure_ascii=False, indent=2)
    store_path = get_correct_path(filename)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    # Print a message of completed export
    print(f"✅ Export abgeschlossen – {filename} erstellt")


def export_worked_sundays_to_json(engine, filename="worked_sundays.json"):
    """Export the number of worked sundays found within TPersonalKontenJeTag and create a JSON-file."""
    # Write SQL-query to retrieve worked sundays (for November 2024 and 12 months prior)
    query = """SELECT
                p.PersNr,
                p.Name AS name,
                p.Vorname AS firstname,
                COUNT(DISTINCT CAST(pkt.Datum AS DATE)) AS worked_sundays
            FROM TPersonalKontenJeTag pkt
            JOIN TPersonal p ON pkt.RefPersonal = p.Prim
            WHERE
                pkt.RefKonten = 40
                AND pkt.Datum BETWEEN '2023.30.11' AND '2024.30.11'
                --AND DATENAME(WEEKDAY, pkt.Datum) = 'Sonntag'
                AND pkt.Wert > 0
            GROUP BY
                p.PersNr,
                p.Name,
                p.Vorname
            ORDER BY
                worked_sundays DESC;
            """
    df = pd.read_sql(query, engine)

    # Restructure and rename to the desired JSON-output-format
    worked_sundays = df.to_dict(orient="records")
    output_json = {"worked_sundays": worked_sundays}

    # Store JSON-file within given directory
    json_output = json.dumps(output_json, ensure_ascii=False, indent=2)
    store_path = get_correct_path(filename)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    # Print a message of completed export
    print(f"✅ Export abgeschlossen – {filename} erstellt")


# Helper function for export_free_shift_and_vacation_days_json()
def collapse(df, col_name):
    out = (
        df.groupby("Prim")["day"]
        .apply(lambda s: sorted(s.unique().tolist()))
        .to_dict()
    )
    return {k: {col_name: v} for k, v in out.items()}


def export_free_shift_and_vacation_days_json(
    engine, filename="free_shifts_and_vacation_days.json"
):
    """Export the free shifts and vacation daysfound within TPersonalKommtGeht and create a JSON-file."""

    EMP_FILE = get_correct_path("employees.json")
    with open(EMP_FILE, encoding="utf-8") as f:
        emp_data = json.load(f)["employees"]

    prim2meta = {
        int(e["Prim"]): {"name": e["name"], "firstname": e["firstname"]}
        for e in emp_data
    }

    whitelist = set(prim2meta)

    query_vac = """
        SELECT
            p.Prim       AS Prim,  
            p.Name       AS name,
            p.Vorname    AS firstname,
            pkg.Datum    AS vacation_days
        FROM TPlanPersonalKommtGeht pkg
        JOIN TPersonal p ON pkg.RefPersonal = p.Prim
        WHERE
            pkg.Datum BETWEEN '2024.01.11' AND '2024.30.11'
            AND pkg.RefgAbw IN (20, 2434, 2435, 2091);
            """

    query_forb_days = """
        SELECT
            p.Prim       AS Prim,  
            p.Name       AS 'name',
            p.Vorname    AS 'firstname',
            pkg.Datum    AS 'forbidden_days'
        FROM TPlanPersonalKommtGeht pkg
        JOIN TPersonal p ON pkg.RefPersonal = p.Prim
        WHERE pkg.Datum BETWEEN '2024.01.11' AND '2024.30.11'
            AND pkg.RefgAbw NOT IN (20, 2434, 2435, 2091)
            """

    query_forb_shifts = """
        SELECT
            p.Prim       AS Prim,  
            p.Name       AS 'name',
            p.Vorname    AS 'firstname',
            pkg.Datum    AS 'reserved',
			d.KurzBez    AS 'dienst'
        FROM TPlanPersonalKommtGeht pkg
        JOIN TPersonal p ON pkg.RefPersonal = p.Prim
		JOIN TDienste d ON pkg.RefDienste = d.Prim
        WHERE pkg.Datum BETWEEN '2024.01.11' AND '2024.30.11'
            AND pkg.RefgAbw IS NULL
            """

    query_acc = """
        SELECT
            RefPersonal     AS Prim,
            Datum
        FROM  TPersonalKontenJeTag
        WHERE RefPlanungsEinheiten = 77
        AND Datum BETWEEN '2024.01.11' AND '2024.30.11';
        """

    vac_df = pd.read_sql(query_vac, engine)
    forb_df = pd.read_sql(query_forb_days, engine)
    shift_df = pd.read_sql(query_forb_shifts, engine)
    acc_df = pd.read_sql(query_acc, engine)

    vac_df = vac_df[vac_df["Prim"].isin(whitelist)]
    forb_df = forb_df[forb_df["Prim"].isin(whitelist)]
    shift_df = shift_df[shift_df["Prim"].isin(whitelist)]

    vac_df["day"] = pd.to_datetime(vac_df["vacation_days"]).dt.day
    forb_df["day"] = pd.to_datetime(forb_df["forbidden_days"]).dt.day
    shift_df["day"] = pd.to_datetime(shift_df["reserved"]).dt.day

    acc_df["Prim"] = acc_df["Prim"].astype(int)
    acc_df["day"] = pd.to_datetime(acc_df["Datum"]).dt.day

    # all days (DatetimeIndex)
    all_dates = pd.date_range(start="2024-11-01", end="2024-11-30", freq="D")

    # only index of day
    all_days = set(all_dates.day)

    vac_map = collapse(vac_df, "vacation_days")
    forb_map = collapse(forb_df, "forbidden_days")

    # reserved:  List[ [day, KurzBez] ] – remove duplicates
    shift_map = (
        shift_df.groupby("Prim")
        .apply(lambda g: sorted({(d, kb) for d, kb in zip(g["day"], g["dienst"])}))
        .to_dict()
    )
    shift_map = {
        k: {"reserved": [[d, kb] for d, kb in v]} for k, v in shift_map.items()
    }

    # Mapping  Prim -> Set (present days in Konto)
    konto_map = acc_df.groupby("Prim")["day"].apply(set).to_dict()
    
    for prim_person in whitelist:

        kontotage = konto_map.get(prim_person, set())  
        fehlende = sorted(all_days - kontotage)

        rec = forb_map.setdefault(prim_person, {"forbidden_days": []})
        # merge (without duplicates) + sort
        rec["forbidden_days"] = sorted(set(rec["forbidden_days"]) | set(fehlende))

        
    employees_out = []
    for prim, meta in prim2meta.items():
        vac = vac_map.get(prim, {}).get("vacation_days", [])
        forb = forb_map.get(prim, {}).get("forbidden_days", [])
        shift = shift_map.get(prim, {}).get("reserved", [])

        # remove duplicates of forbidden days that are already in forbidden shifts
        shift_days = {d for d, _ in shift}
        forb_clean = [d for d in forb if d not in shift_days]

        rec = {
            "Prim": prim,
            "name": meta["name"],
            "firstname": meta["firstname"],
            "vacation_days": vac,
            "forbidden_days": forb_clean,
            "reserved": shift,
        }
        employees_out.append(rec)

    # Restructure and rename to the desired JSON-output-format
    free_shifts_and_vacation_days = employees_out
    output_json = {"employees": free_shifts_and_vacation_days}

    # Store JSON-file within given directory
    json_output = json.dumps(output_json, ensure_ascii=False, indent=2, default=str)
    store_path = get_correct_path(filename)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    # Print a message of completed export
    print(f"✅ Export abgeschlossen – {filename} erstellt")
