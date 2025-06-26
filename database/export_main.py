from dotenv import load_dotenv
from connection_setup import get_db_engine
import export_data

# Load the .env-file for login purposes
load_dotenv()


def main(plan_id=17193):
    """Sets up a basic connection to the TimeOffice database and exports all needed data for the algorithm."""
    engine = get_db_engine()
    base_data = export_data.export_planning_data(engine, plan_id)

    export_data.export_personal_data_to_json(engine, plan_id)
    export_data.export_target_working_minutes_to_json(engine, base_data["JahrMonat"])
    export_data.export_worked_sundays_to_json(
        engine, base_data["MinusEinJahr"], base_data["BisDat"]
    )
    export_data.export_free_shift_and_vacation_days_json(
        engine, plan_id, base_data["PE"]
    )


if __name__ == "__main__":
    main()
