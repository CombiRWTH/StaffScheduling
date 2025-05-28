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
    """Export all personal staff information found within TPersonal and create a JSON-file.
    CURRENTLY ONLY TEST PURPOSE ON THIS BRANCH"""
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
    json_output = df.to_json(orient="records", force_ascii=False)
    store_path = get_correct_path(filename)
    # Create or overwrite file in target directory
    with open(store_path, "w", encoding="utf-8") as f:
        f.write(json_output)
    print(f"✅ Export abgeschlossen – {filename} erstellt")


def main():
    conn = get_db_connection()

    export_personal_data_to_json(conn)


if __name__ == "__main__":
    main()
