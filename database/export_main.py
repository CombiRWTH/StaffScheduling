from dotenv import load_dotenv
from connection_setup import get_db_engine
import export_data

# Load the .env-file for login purposes
load_dotenv()


def main(planning_unit=77, from_date="2024-11-01", till_date="2024-11-30"):
    """Sets up a basic connection to the TimeOffice database and exports all needed data for the algorithm."""
    engine = get_db_engine()
    base_data = export_data.export_planning_data(
        engine, planning_unit, from_date, till_date
    )

    export_data.export_personal_data_to_json(engine, base_data["plan_id"])
    export_data.export_target_working_minutes_to_json(engine, base_data["year_month"])
    export_data.export_worked_sundays_to_json(
        engine, base_data["minus_a_year"], base_data["till_date"]
    )
    export_data.export_free_shift_and_vacation_days_json(
        engine, base_data["plan_id"], base_data["planning_unit"]
    )


if __name__ == "__main__":
    main()
