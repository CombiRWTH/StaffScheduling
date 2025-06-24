from dotenv import load_dotenv
from connection_setup import get_db_connection
import export_data

# Load the .env-file for login purposes
load_dotenv()


def main():
    """Sets up a basic connection to the TimeOffice database and exports all of the needed data for the algorithm."""
    conn = get_db_connection()

    export_data.export_personal_data_to_json(conn)
    export_data.export_target_working_minutes_to_json(conn)
    export_data.export_worked_sundays_to_json(conn)
    export_data.export_free_shift_and_vacation_days_json(conn)

if __name__ == "__main__":
    main()
