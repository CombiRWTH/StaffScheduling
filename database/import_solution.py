import json, ast, pyodbc, os, re, unicodedata
import pandas as pd
from datetime import datetime, date, time, timedelta
from dotenv import load_dotenv
from itertools import chain, product
from collections import Counter, defaultdict

# Load the .env-file for login purposes
load_dotenv()


#Returns the sql connection string
def get_conn_string():
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
    return conn_str



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




# Load JSON files
JSON_FILE = "solutions_test.json"
with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

EMP_FILE = "employees.json"
with open(EMP_FILE, encoding="utf-8") as f:
    emp_data = json.load(f)["employees"] 



# Help functions
def norm(s: str) -> str:
    """Lower case, Unicode normalization, merge spaces"""
    s = unicodedata.normalize("NFKD", s)
    return re.sub(r"\s+", " ", s).strip().lower()

def variants(last: str, first: str):
    """Generates common spellings of a name pair."""
    raw = [
        f"{last} {first}", f"{first} {last}",
        f"{last}, {first}", f"{first}, {last}",
    ]
    return [norm(x) for x in raw]

def load_person_to_job(conn_str: str) -> dict[int, int]:
    """Reads TPersonal (Prim, RefBerufe) and returns {Prim: RefBerufe}."""
    sql = "SELECT Prim, RefBerufe FROM TPersonal"
    with pyodbc.connect(conn_str) as cn:
        return {row.Prim: row.RefBerufe for row in cn.cursor().execute(sql)}

conn_str = get_conn_string()
prim_to_refberuf = load_person_to_job(conn_str)



# Check surname uniqueness
last_counts = Counter(norm(e["name"]) for e in emp_data)
unique_last = {ln for ln, c in last_counts.items() if c == 1}



# Build Key-→ Prim-Table 
key2prim = {}

for emp in emp_data:
    ln, fn, prim = norm(emp["name"]), norm(emp["firstname"]), emp["Prim"]

    # full name variant
    for v in variants(ln, fn):
        key2prim[v] = prim

    # only last name
    if ln in unique_last:
        key2prim[ln] = prim



# Determine Index → Prim 
idx_to_name = data["employees"]["name_to_index"]
idx_to_prim, unmatched = {}, []

for full_name, idx in idx_to_name.items():
    key = norm(full_name)
    prim = key2prim.get(key)

    if prim is not None:
        idx_to_prim[idx] = prim
    else:
        unmatched.append(full_name)



# Check result
if unmatched:
    print("Not yet assigned:", ", ".join(unmatched))
else:
    print("All names successfully mapped!")



# Shift-Mapping
# Format: shift_id : [ (von_time, bis_time, day_offset) , … ]
SHIFT_SEGMENTS = {
    # Frühdienst
    0: [
        (time( 6,  0), time(10,  0), 0),
        (time(10, 30), time(14, 10), 0),   
    ],
    # Spätdienst
    1: [
        (time(12, 50), time(15, 30), 0),
        (time(16,  0), time(21,  0), 0),
    ],
    # Nachtdienst (Segment 3 ends on the next day)
    2: [
        (time(20, 20), time(21, 45), 0),
        (time(22,  0), time(23, 30), 0),
        (time( 0,  0), time( 6, 30), 1),   # +1 day
    ],
    # Zwischendienst
    3: [
        (time(8, 0), time(14, 0), 0),
        (time(12,  30), time(16, 10), 0),
    ],
}



PE_ID = 77  #PlanungseinheitID
PLAN_ID   = 17193      #RefPlan
STATUS_ID = 20      

# corresponding shift IDs
SHIFT_TO_REFDIENST = {0: 2939, 1: 2947, 2: 2953, 3: 2906}



# Build solution in DataFrame  (one row per segment)
records = []
for key, val in data["solutions"][0].items():     # 0 = first found solution
    if val != 1:
        continue

    emp_idx, date_str, shift_id = ast.literal_eval(key)
    base_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    ref_dienst = SHIFT_TO_REFDIENST[shift_id]

    prim_person = idx_to_prim[emp_idx]  
    prim_beruf = prim_to_refberuf.get(prim_person)
    if prim_beruf is None:
        raise ValueError(f"Kein RefBerufe für Personal-Prim {prim_person}")

    for seg_idx, (von_t, bis_t, offset) in enumerate(SHIFT_SEGMENTS[shift_id], start=1):
        datum      = base_date + timedelta(days=offset)
        von_dt     = datetime.combine(datum, von_t)
        bis_dt     = datetime.combine(datum, bis_t)
        dauer_min = int((bis_dt - von_dt).total_seconds() // 60) 

        records.append({
            "RefPlan":      PLAN_ID,
            "RefPersonal":  prim_person,
            "Datum":        datum,
            "RefStati":     STATUS_ID,
            "lfdNr":        0,   
            "RefgAbw":      None,
            "RefDienste":   ref_dienst,
            "RefBerufe":    prim_beruf,
            "RefPlanungseinheiten": PE_ID,
            "VonZeit":      von_dt,
            "BisZeit":      bis_dt,
            "RefDienstAbw": None,
            "Minuten":      dauer_min,
            "Info":         None,
            "RefEinsatzArten": None,
            "Wunschdienst": None,
            "BereitVon":    None,
            "BereitBis":    None,
            "RefDiensteSpezTypenElemente": None,
            "RefPeinheitOwner": PE_ID,
            "RefSeminareTermine": None,
            "VBAHerkunft": None,
        })

df = pd.DataFrame(records)



# lfdNr assigned per day/employee/status
df["lfdNr"] = (
    df.sort_values(["RefPersonal", "Datum", "VonZeit"])
      .groupby(["RefPersonal", "Datum", "RefStati"])
      .cumcount() + 1
)



# Test export as a json file to check if the output is correct without actually writing into the db
'''
test_file = df.to_dict(orient="records")
output_json = {
     "test": test_file
    }

filename = "test_file.json"

# Store JSON-file within given directory
json_output = json.dumps(output_json, ensure_ascii=False, indent=2, default=str)
store_path = get_correct_path(filename)
with open(store_path, "w", encoding="utf-8") as f:
    f.write(json_output)
# Print a message of completed export
print(f"✅ Export abgeschlossen – {filename} erstellt")
'''


# pyodbc-Connection + Bulk-Insert
conn_str = get_conn_string()

with pyodbc.connect(conn_str) as conn:
    cursor = conn.cursor()
    cursor.fast_executemany = True      # bulk-optimized

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
            row.RefPlan, row.RefPersonal, row.Datum, row.RefStati, row.lfdNr,
            row.RefgAbw, row.RefDienste, row.RefBerufe, row.RefPlanungseinheiten,
            row.VonZeit, row.BisZeit, row.RefDienstAbw, row.Minuten, row.Info, 
            row.RefEinsatzArten, row.Wunschdienst, row.BereitVon, row.BereitBis,
            row.RefDiensteSpezTypenElemente, row.RefPeinheitOwner, 
            row.RefSeminareTermine, row.VBAHerkunft
        )
        for row in df.itertuples(index=False)
    ]

    cursor.executemany(insert_sql, params)
    conn.commit()


print(f"{len(df):,} Lines inserted in TPlanPersonalKommtGeht.")
