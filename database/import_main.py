from dotenv import load_dotenv
from connection_setup import get_db_engine
from datetime import date
import import_solution
import export_data
import logging
import json
import pandas as pd

# Load the .env-file for login purposes
load_dotenv()


def main(planning_unit=77, from_date=date(2024, 11, 1), till_date=date(2024, 11, 30)):
    """Sets up a basic connection to the TimeOffice database and imports the solution found by the algorithm."""
    engine = get_db_engine()

    base_data = export_data.export_planning_data(
        engine, planning_unit, from_date, till_date
    )

    data, emp_data = import_solution.load_json_files(from_date, till_date, planning_unit)
    prim_to_refberuf = import_solution.load_person_to_job(engine)
    planned_map = import_solution.load_planned_shifts() 

    PE_ID = planning_unit
    PLAN_ID = base_data["plan_id"]
    STATUS_ID = 20 # Always "Sollplanung" as we only generate such plans

    # Corresponding shift IDs to given counts of shifts
    SHIFT_TO_REFDIENST = {0: 2939, 1: 2947, 2: 2953, 3: 2906}
    # Shift mapping with format: shift_id : [ (von_time, bis_time, day_offset) , … ]
    SHIFT_SEGMENTS = import_solution.load_shift_segments(engine, SHIFT_TO_REFDIENST)

    df = import_solution.build_dataframe(
        data,
        emp_data,
        prim_to_refberuf,
        SHIFT_SEGMENTS,
        SHIFT_TO_REFDIENST,
        PE_ID,
        PLAN_ID,
        STATUS_ID,
        planned_map
    )

    action = input("Press i for importing, d for deleting or j to generate a test json:")

    match action:
        case "i":
            # When needed to write into the database directly:
            import_solution.insert_dataframe_to_db(df, engine)
        case "d":
            # When needed to delete from the database directly:
            import_solution.delete_dataframe_from_db(df, engine)
        case "j":
            # Test export as a json file to check if the output is correct without actually writing into the db:
            test_file = df.to_dict(orient="records")
            output_json = {"test": test_file}

            filename = "test_file.json"

            # Store JSON-file within given directory
            json_output = json.dumps(output_json, ensure_ascii=False, indent=2, default=str)
            store_path = import_solution.get_correct_path(filename)
            with open(store_path, "w", encoding="utf-8") as f:
                f.write(json_output)
            # Print a message of completed export
            logging.info(f"✅ Export abgeschlossen – {filename} erstellt")



if __name__ == "__main__":
    main()
