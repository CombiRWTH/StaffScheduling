import pandas as pd
import json
import os
import logging
from dateutil.relativedelta import relativedelta

logging.basicConfig(level=logging.INFO)


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


def export_planning_data(engine, planning_unit, from_date, till_date):
    """Export relevant basic plan data for retrieving all information for the algorithm.
	
 	Args:
        	engine: SQLAlchemy database engine used to execute queries.
        	planning_unit: ID of the planning unit to filter the data.
        	from_date: Start date (string in 'YYYY-MM-DD' format).
        	till_date: End date (string in 'YYYY-MM-DD' format).

	Returns:
        	dict: Dictionary containing plan data
	 
    """
    
    # Construct and execute a SQL query to retrieve planning data within the given date range
    query = f"""SELECT
                    Prim AS 'plan_id',
                    RefPlanungseinheiten AS 'planning_unit',
                    VonDat AS 'from_date',
                    BisDat AS 'till_date'
                FROM TPlan
                WHERE RefPlanungseinheiten = {planning_unit}
                AND VonDat = CONVERT(date,'{from_date}',23)
                AND BisDat = CONVERT(date,'{till_date}',23)
            """
    df = pd.read_sql(query, engine)
    result = df.iloc[0].to_dict()

    # Construct a string in 'YYYYMM' format from the from_date
    year_month = f"{pd.Timestamp(from_date).year}{pd.Timestamp(from_date).month:02d}"
    result["year_month"] = year_month
    
    # Calculate the date one year before till_date and store it in 'YYYY-DD-MM' format
    one_year_back = pd.Timestamp(till_date) - relativedelta(years=1)
    result["minus_a_year"] = (
        f"{one_year_back.year}-{one_year_back.day:02d}-{one_year_back.month:02d}"
    )
    
    # Reformat from_date and till_date into 'YYYY-DD-MM' format for consistency
    result["from_date"] = (
        f"{pd.Timestamp(from_date).year}-{pd.Timestamp(from_date).day:02d}-{pd.Timestamp(from_date).month:02d}"
    )
    result["till_date"] = (
        f"{pd.Timestamp(till_date).year}-{pd.Timestamp(till_date).day:02d}-{pd.Timestamp(till_date).month:02d}"
    )

    return result


def export_shift_data_to_json(engine, filename="shift_information.json"):
    """Export all shift related information such as times and breaks and create a JSON-file.
	
 	Args:
        	engine: SQLAlchemy engine used for executing the database query.
        	filename (str): Name of the output JSON file (default: 'shift_information.json').
    
    """
    
    # Define relevant shift types with their associated IDs and shorthand names
    shift_ids = {
        "Frühschicht": {"id": "2939", "name": "F2_"},
        "Spätschicht": {"id": "2947", "name": "S2_"},
        "Nachtschicht": {"id": "2953", "name": "N2_"},
        "Zwischendienst": {"id": "2906", "name": "T75_"},
        "Sonderdienst": {"id": "1406", "name": "Z60"},
    }
    shift_id_to_name = {v["id"]: v["name"] for v in shift_ids.values()}
    
    # SQL query to retrieve planned shift times for the relevant shift types
    query = f"""SELECT
                    RefDienste AS 'shift_id',
                    Kommt AS 'start',
                    Geht AS 'end'
                FROM TDiensteSollzeiten
                WHERE RefDienste = '{shift_ids["Frühschicht"]["id"]}'
                OR RefDienste = '{shift_ids["Spätschicht"]["id"]}'
                OR RefDienste = '{shift_ids["Nachtschicht"]["id"]}'
                OR RefDienste = '{shift_ids["Zwischendienst"]["id"]}'
                OR RefDienste = '{shift_ids["Sonderdienst"]["id"]}'
            """
    df = pd.read_sql(query, engine)

    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    df = df.sort_values(["shift_id", "start"])

    # Compute total working minutes of shift
    df["working_minutes"] = (df["end"] - df["start"]).dt.total_seconds() / 60

    # Compute total pause duration of shift
    df["pause"] = df.groupby("shift_id")["start"].shift(-1) - df["end"]
    df["pause_min"] = df["pause"].dt.total_seconds() / 60
    df["pause_min"] = df["pause_min"].fillna(0)

    # Group by shift type and aggregate all given values
    agg = (
        df.groupby("shift_id")
        .agg(
            start_time=("start", "min"),
            end_time=("end", "max"),
            working_minutes=("working_minutes", "sum"),
            break_duration=("pause_min", "sum"),
        )
        .reset_index()
    )
    
    # Compute total duration from first start to last end (not subtracting breaks)
    agg["shift_duration"] = (
        agg["end_time"] - agg["start_time"]
    ).dt.total_seconds() / 60
    agg["shift_id"] = agg["shift_id"].astype(str)
    agg["shift_name"] = agg["shift_id"].map(shift_id_to_name).fillna("unknown")
    agg["start_time"] = agg["start_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")
    agg["end_time"] = agg["end_time"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    # Store JSON-file within given directory
    json_output = json.dumps(
        agg.to_dict(orient="records"), ensure_ascii=False, indent=2
    )
    store_path = get_correct_path(filename)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    # Log a message of completed export
    logging.info(f"✅ Export abgeschlossen – {filename} erstellt")


def export_personal_data_to_json(engine, plan_id, filename="employees.json"):
    """Export all personal staff information found within TPersonal and create a JSON-file.
    	Args:
        	engine: SQLAlchemy engine object used to connect to the database.
        	plan_id (int): ID of the plan for which staff data should be exported.
        	filename (str): Name of the JSON file to be created (default: 'employees.json').
    
    """
    
    # Write SQL-query to retrieve personal data linked to a specific plan ID
    query = f"""SELECT
                    a.Prim,
                    a.Name,
                    a.Vorname,
                    t.Bezeichnung AS 'Beruf'
                FROM TPlanPersonal b
                JOIN
                    TPersonal a ON b.RefPersonal = a.Prim
                LEFT JOIN
                    TBerufe t ON a.RefBerufe = t.Prim
                WHERE RefPlan = {plan_id}
            """
    df = pd.read_sql(query, engine)
    df = df.drop_duplicates()

    # Restructure and rename to the desired JSON-output-format
    df_renamed = df.rename(
        columns={
            "Prim": "key",
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
    # Log a message of completed export
    logging.info(f"✅ Export abgeschlossen – {filename} erstellt")


def export_target_working_minutes_to_json(
    engine, month, filename="target_working_minutes.json"
):
    """Export all target working minutes found within TPersonalKontenJeMonat and create a JSON-file.

 	Args:
        	engine: SQLAlchemy engine object used to connect to the database.
        	month (int): Numeric representation of the target month (e.g., 202411 for November 2024).
        	filename (str): Name of the JSON file to be created (default: 'target_working_minutes.json').
    
    """
    
    # SQL Query to export the target working hours from TPersonalKontenJeMonat
    query = f"""SELECT
                    p.Prim,
                    p.Name AS 'name',
                    p.Vorname AS 'firstname',
                    pkt.RefKonten,
                    pkt.Wert2
                FROM TPersonalKontenJeMonat pkt
                JOIN TPersonal p ON pkt.RefPersonal = p.Prim
                WHERE (pkt.RefKonten = 1  OR pkt.RefKonten = 19 OR pkt.RefKonten = 55) AND pkt.Monat = {month} ORDER BY p.Name asc"""

    df = pd.read_sql(query, engine)

    # Convert hours (Wert2) to minutes and round to nearest whole number
    df["Wert2"] = (df["Wert2"] * 60).round(0)

    # Merging different entries for each employee to summarize all Konten in one entry
    df_wide = (
        df.pivot_table(
            index=["Prim", "name", "firstname"],
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
        columns={
            "Wert_RefKonten1": "target",
            "Wert_RefKonten19_55": "actual",
            "Prim": "key",
        }
    )

    target_working_minutes_list = df_wide.to_dict(orient="records")
    output_json = {"target_working_minutes": target_working_minutes_list}

    # Store JSON-file within given directory
    json_output = json.dumps(output_json, ensure_ascii=False, indent=2)
    store_path = get_correct_path(filename)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    # Log a message of completed export
    logging.info(f"✅ Export abgeschlossen – {filename} erstellt")


def export_worked_sundays_to_json(
    engine, from_date, till_date, filename="worked_sundays.json"
):
    """Export the number of worked sundays found within TPersonalKontenJeTag and create a JSON-file.
    
	Args:
        	engine: SQLAlchemy engine object to connect to the database.
        	from_date (str): Start date (inclusive) of the period to query, format 'YYYY/DD/MM'.
        	till_date (str): End date (inclusive) of the period to query, format 'YYYY/DD/MM'.
        	filename (str): Name of the JSON output file (default: 'worked_sundays.json').
    
    """
    
    # Write SQL-query to retrieve worked sundays (for November 2024 and 12 months prior)
    query = f"""SELECT
                p.Prim AS 'key',
                p.Name AS name,
                p.Vorname AS firstname,
                COUNT(DISTINCT CAST(pkt.Datum AS DATE)) AS worked_sundays
            FROM TPersonalKontenJeTag pkt
            JOIN TPersonal p ON pkt.RefPersonal = p.Prim
            WHERE
                pkt.RefKonten = 40
                AND pkt.Datum BETWEEN '{from_date}' AND '{till_date}'
                AND DATENAME(WEEKDAY, pkt.Datum) = 'Sonntag'
                AND pkt.Wert > 0
            GROUP BY
                p.Prim,
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
    # Log a message of completed export
    logging.info(f"✅ Export abgeschlossen – {filename} erstellt")


# Helper function for export_free_shift_and_vacation_days_json()
def collapse(df, col_name):
    out = (
        df.groupby("Prim")["day"].apply(lambda s: sorted(s.unique().tolist())).to_dict()
    )
    return {k: {col_name: v} for k, v in out.items()}


def get_plan_dates(engine, plan_id):
    """Retrieve the start and end dates of a plan from the database.

    Args:
        engine: SQLAlchemy engine object to connect to the database.
        plan_id (str or int): The unique identifier (primary key) of the plan in the TPlan table.

    Returns:
        pd.DataFrame: A DataFrame containing one row with 'START' and 'END' columns as DATE objects.
    """
    query = f"""
        SELECT
            CAST(VonDat AS DATE) AS 'START',
            CAST(BisDat AS DATE) AS 'END'
        FROM TPlan WHERE Prim = '{plan_id}'
        """
    df = pd.read_sql(query, engine)
    return df


def export_free_shift_and_vacation_days_json(
    engine, plan_id, planning_unit, filename="free_shifts_and_vacation_days.json"
):
    """Export the free shifts and vacation daysfound within TPersonalKommtGeht and create a JSON-file.
    
    	Args:
        	engine: SQLAlchemy engine object to connect to the database.
        	plan_id (int or str): The unique identifier for the plan.
        	planning_unit (int or str): Identifier for the planning unit to filter employees.
        	filename (str, optional): Output JSON file name. Defaults to 'free_shifts_and_vacation_days.json'.
    """
    
    # Fetch the plan's start and end dates from the database
    dates = get_plan_dates(engine, plan_id)

    START_DATE = dates.loc[0, "START"]
    END_DATE = dates.loc[0, "END"]

    EMP_FILE = get_correct_path("employees.json")
    with open(EMP_FILE, encoding="utf-8") as f:
        emp_data = json.load(f)["employees"]

    prim2meta = {
        int(e["key"]): {"name": e["name"], "firstname": e["firstname"]}
        for e in emp_data
    }

    whitelist = set(prim2meta)
    
    # Query for vacation days (specific codes in RefgAbw)
    query_vac = f"""
        SELECT
            p.Prim       AS Prim,
            p.Name       AS name,
            p.Vorname    AS firstname,
            pkg.Datum    AS vacation_days
        FROM TPlanPersonalKommtGeht pkg
        JOIN TPersonal p ON pkg.RefPersonal = p.Prim
        WHERE
            pkg.Datum BETWEEN CONVERT(date,'{START_DATE}',23) AND CONVERT(date,'{END_DATE}',23)
            AND pkg.RefgAbw IN (20, 2434, 2435, 2091);
            """
   
    # Query for forbidden days (all entries that are NOT vacation but still blocked availability)
    query_forb_days = f"""
        SELECT
            p.Prim       AS Prim,
            p.Name       AS 'name',
            p.Vorname    AS 'firstname',
            pkg.Datum    AS 'forbidden_days'
        FROM TPlanPersonalKommtGeht pkg
        JOIN TPersonal p ON pkg.RefPersonal = p.Prim
        WHERE pkg.Datum BETWEEN CONVERT(date,'{START_DATE}',23) AND CONVERT(date,'{END_DATE}',23)
            AND pkg.RefgAbw NOT IN (20, 2434, 2435, 2091)
            """
    
    # Query for planned shifts (RefgAbw is NULL → workday in another unit)
    query_forb_shifts = f"""
        SELECT
            p.Prim       AS Prim,
            p.Name       AS 'name',
            p.Vorname    AS 'firstname',
            pkg.Datum    AS 'planned_shifts',
			d.KurzBez    AS 'dienst'
        FROM TPlanPersonalKommtGeht pkg
        JOIN TPersonal p ON pkg.RefPersonal = p.Prim
		JOIN TDienste d ON pkg.RefDienste = d.Prim
        WHERE pkg.Datum BETWEEN CONVERT(date,'{START_DATE}',23) AND CONVERT(date,'{END_DATE}',23)
            AND pkg.RefgAbw IS NULL
            """
    
    # Query for accounting entries per employee per day
    query_acc = f"""
        SELECT
            RefPersonal     AS Prim,
            Datum
        FROM  TPersonalKontenJeTag
        WHERE RefPlanungsEinheiten = {planning_unit}
        AND Datum BETWEEN CONVERT(date,'{START_DATE}',23) AND CONVERT(date,'{END_DATE}',23);
        """
    
    # Execute all queries
    vac_df = pd.read_sql(query_vac, engine)
    forb_df = pd.read_sql(query_forb_days, engine)
    shift_df = pd.read_sql(query_forb_shifts, engine)
    acc_df = pd.read_sql(query_acc, engine)

    # Filter for relevant employees
    vac_df = vac_df[vac_df["Prim"].isin(whitelist)]
    forb_df = forb_df[forb_df["Prim"].isin(whitelist)]
    shift_df = shift_df[shift_df["Prim"].isin(whitelist)]

    vac_df["day"] = pd.to_datetime(vac_df["vacation_days"]).dt.day
    forb_df["day"] = pd.to_datetime(forb_df["forbidden_days"]).dt.day
    shift_df["day"] = pd.to_datetime(shift_df["planned_shifts"]).dt.day

    acc_df["Prim"] = acc_df["Prim"].astype(int)
    acc_df["day"] = pd.to_datetime(acc_df["Datum"]).dt.day

    # all days (DatetimeIndex)
    all_dates = pd.date_range(start=START_DATE, end=END_DATE, freq="D")

    # only index of day
    all_days = set(all_dates.day)

    vac_map = collapse(vac_df, "vacation_days")
    forb_map = collapse(forb_df, "forbidden_days")

    # planned_shifts:  List[ [day, KurzBez] ] – remove duplicates
    shift_map = (
        shift_df.groupby("Prim")
        .apply(lambda g: sorted({(d, kb) for d, kb in zip(g["day"], g["dienst"])}))
        .to_dict()
    )
    shift_map = {
        k: {"planned_shifts": [[d, kb] for d, kb in v]} for k, v in shift_map.items()
    }

    # Mapping  Prim -> Set (present days in Konto)
    konto_map = acc_df.groupby("Prim")["day"].apply(set).to_dict()

    # Add missing days (present in calendar but not in accounting entries) as forbidden days
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
        shift = shift_map.get(prim, {}).get("planned_shifts", [])

        # remove duplicates of forbidden days that are already in forbidden shifts
        shift_days = {d for d, _ in shift}
        forb_clean = [d for d in forb if d not in shift_days]

        rec = {
            "key": prim,
            "name": meta["name"],
            "firstname": meta["firstname"],
            "vacation_days": vac,
            "forbidden_days": forb_clean,
            "planned_shifts": shift,
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
    # Log a message of completed export
    logging.info(f"✅ Export abgeschlossen – {filename} erstellt")
