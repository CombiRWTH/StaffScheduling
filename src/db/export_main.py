from datetime import date

from . import export_data
from .connection_setup import get_db_engine


def main(planning_unit: int = 77, from_date: date = date(2024, 11, 1), till_date: date = date(2024, 11, 30)):
    """Sets up a basic connection to the TimeOffice database and exports all needed data for the algorithm."""
    engine = get_db_engine()
    base_data = export_data.export_planning_data(engine, planning_unit, from_date, till_date)
    export_data.export_shift_data_to_json(engine, planning_unit)

    export_data.export_personal_data_to_json(engine, planning_unit, base_data["plan_id"])
    export_data.export_target_working_minutes_to_json(engine, planning_unit, base_data["year_month"])
    export_data.export_worked_sundays_to_json(engine, planning_unit, base_data["minus_a_year"], base_data["till_date"])
    export_data.export_free_shift_and_vacation_days_json(engine, planning_unit, base_data["plan_id"])


if __name__ == "__main__":
    main()
