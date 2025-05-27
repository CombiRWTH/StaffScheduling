import pyodbc
import pandas as pd
from dotenv import load_dotenv
import os
import json

# .env-Datei laden
load_dotenv()

print("Verfügbare Treiber:", pyodbc.drivers())
# Umgebungsvariablen auslesen
server = os.getenv("DB_SERVER")
database = os.getenv("DB_NAME")
username = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

# SQL-Verbindung aufbauen
conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "TrustServerCertificate=yes;"
)
conn = pyodbc.connect(conn_str)

# SQL-Test-Abfrage
query = "SELECT * FROM TPersonal WHERE Prim=459"
df = pd.read_sql(query, conn)

# In JSON konvertieren
json_output = df.to_json(orient="records", force_ascii=False)

# In Datei schreiben
with open("daten_export.json", "w", encoding="utf-8") as f:
    f.write(json_output)

print("✅ Export abgeschlossen – daten_export.json erstellt")