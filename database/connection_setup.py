import pyodbc
import pandas as pd
from dotenv import load_dotenv
import os
import json

# Load the .env-file for login purposes
load_dotenv()


def get_db_connection():
    """Create a basic connection to the TimeOffice database."""
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(conn_str)


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


def export_personal_data_to_json(conn, filename="employees.json"):
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
    df = pd.read_sql(query, conn)

    # Restructure and rename to the desired JSON-output-format
    df_renamed = df.rename(columns={
        "PersNr": "PersNr",
        "Vorname": "firstname",
        "Name": "name",
        "Beruf": "type"
    })
    employees_list = df_renamed.to_dict(orient="records")
    output_json = {
        "employees": employees_list
    }

    # Store JSON-file within given directory
    json_output = json.dumps(output_json, ensure_ascii=False, indent=2)
    store_path = get_correct_path(filename)
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    # Print a message of completed export
    print(f"✅ Export abgeschlossen – {filename} erstellt")


def export_target_working_minutes_to_json(conn, filename="target_working_minutes.json"):
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

    df = pd.read_sql(query, conn)

    # Converting hours to minutes
    df["Wert2"] = (df["Wert2"] * 60).round(0)

    # Merging different entries for each employee to summarize all Konten in one entry
    df_wide = (
        df.pivot_table(index=["PersNr", "name", "firstname"],
                       columns="RefKonten",
                       values="Wert2",
                       aggfunc="sum",
                       fill_value=0)
          .reset_index()
          .rename(columns=lambda c: f"Wert_RefKonten{c}" if isinstance(c, (int, float)) else c)
    )

    # Choosing right Konto (see DatabaseQueries.md)
    df_wide["Wert_RefKonten19_55"] = df_wide[["Wert_RefKonten19",
                                          "Wert_RefKonten55"]].max(axis=1)
    
    # 
    df_wide = df_wide.drop(columns=["Wert_RefKonten19", "Wert_RefKonten55"])

    # Renaming Columns 
    df_wide = df_wide.rename(columns={
    "Wert_RefKonten1":      "target",
    "Wert_RefKonten19_55":  "actual"
    })

    json_output = df_wide.to_json(orient="records", force_ascii=False)
    store_path = get_correct_path(filename)

    # Create or overwrite file in target directory
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    print(f"✅ Export abgeschlossen – {filename} erstellt")


def main():
    conn = get_db_connection()

    export_personal_data_to_json(conn)
    export_target_working_minutes_to_json(conn)


if __name__ == "__main__":
    main()
