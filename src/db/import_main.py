import json
import logging
from datetime import date

from . import export_data, import_solution
from .connection_setup import get_db_engine


def main(
    planning_unit: int = 77,  # Default planning unit ID
    from_date: date = date(2024, 11, 1),  # Planning period start date
    till_date: date = date(2024, 11, 30),  # Planning period end date
    cli_input: str | None = None,  # Optional user input for action type
):
    """Sets up a basic connection to the TimeOffice database and imports the solution found by the algorithm."""
    engine = get_db_engine()

    # Load base data of generated plan
    base_data = export_data.export_planning_data(engine, planning_unit, from_date, till_date)

    # Load solution and employee json
    data, emp_data = import_solution.load_json_files(from_date, till_date, planning_unit)

    # Load mapping of employee to their job and their already planned shifts
    prim_to_refberuf = import_solution.load_person_to_job(engine)
    planned_map = import_solution.load_planned_shifts(planning_unit)

    PE_ID = planning_unit
    PLAN_ID = base_data["plan_id"]
    STATUS_ID = 20  # Always "Sollplanung" as we only generate such plans

    # Corresponding shift IDs to given counts of shifts
    # 2939: F2_ (Frühschicht), 2906: T75_ (Zwischendienst),
    # 2947: S2_ (Spätschicht), 2953: N2_ (Nachtschicht), 1406: Z60 (Sonderschicht)
    SHIFT_TO_REFDIENST = {0: 2939, 1: 2906, 2: 2947, 3: 2953, 4: 1406}

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
        planned_map,
    )

    if cli_input is None:
        # User input to determine between inserting/deleting/generating test json
        action = input("Press i for importing, d for deleting or j to generate a test json:")
    elif cli_input in ["i", "d", "j"]:
        action = cli_input
    else:
        raise ValueError(f"{cli_input} is not a valid value for 'cli_input'.\nAccepted values are 'i', 'd', 'j', None.")

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
            logging.info(f"Export abgeschlossen – {filename} erstellt")


if __name__ == "__main__":
    main()
