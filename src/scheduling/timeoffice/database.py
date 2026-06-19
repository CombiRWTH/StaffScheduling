import logging

from sqlalchemy import URL, Engine, create_engine

from scheduling.domain import PlanningPeriod
from scheduling.settings import Settings
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.repositories import TimeOfficeRepositories
from scheduling.validation.dataset import ValidatedSchedulingDataset

logger = logging.getLogger(__name__)


def create_db_engine(settings: Settings) -> Engine:
    """Build the SQLAlchemy Engine for the TimeOffice SQL Server database."""
    url = URL.create(
        drivername="mssql+pyodbc",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_server,
        database=settings.db_name,
        query={
            "driver": settings.db_driver,
            "TrustServerCertificate": "yes",
        },
    )

    return create_engine(url)


class TimeOfficeDatabase:
    """Loads reduced scheduling data from TimeOffice.

    This class owns the database connection boundary and repository call order.
    It does not contain solver logic or TimeOffice row mapping details.
    """

    def __init__(
        self,
        *,
        engine: Engine,
        repositories: TimeOfficeRepositories,
        facts: TimeOfficeFacts,
    ) -> None:
        self._engine = engine
        self._repositories = repositories
        self._facts = facts

    def fetch_dataset(
        self,
        *,
        selected_planning_unit_ids: tuple[int, ...],
        period: PlanningPeriod,
    ) -> ValidatedSchedulingDataset:
        if not selected_planning_unit_ids:
            raise ValueError("At least one planning unit must be selected.")

        with self._engine.connect() as connection:
            planning_unit_result = self._repositories.planning_units.fetch(
                connection=connection,
                selected_planning_unit_ids=selected_planning_unit_ids,
                period=period,
            )

            planning_unit_ids = tuple(
                planning_unit.planning_unit_id for planning_unit in planning_unit_result.planning_units
            )

            personnel_result = self._repositories.personnel.fetch(
                connection=connection,
                plans=planning_unit_result.plans,
                planning_unit_ids=planning_unit_ids,
                period=period,
            )

            shift_result = self._repositories.shifts.fetch(
                connection=connection,
            )

            roster_result = self._repositories.roster.fetch(
                connection=connection,
                plans=planning_unit_result.plans,
                employees=personnel_result.employees,
                period=period,
            )

            demand_result = self._repositories.demand.fetch(
                connection=connection,
                period=period,
                planning_units=planning_unit_result.planning_units,
                shifts=shift_result.shifts,
            )

            sunday_work_history_result = self._repositories.sunday_work_history.fetch(
                connection=connection,
                period=period,
                employees=personnel_result.employees,
            )

            wish_result = self._repositories.wishes.fetch(
                connection=connection,
                plans=planning_unit_result.plans,
                employees=personnel_result.employees,
                shifts=shift_result.shifts,
                period=period,
            )

            monthly_work_account_result = self._repositories.monthly_work_accounts.fetch(
                connection=connection,
                employees=personnel_result.employees,
                period=period,
            )

        return ValidatedSchedulingDataset(
            period=period,
            planning_units=planning_unit_result.planning_units,
            plans=planning_unit_result.plans,
            employees=personnel_result.employees,
            plan_participants=personnel_result.plan_participants,
            planning_unit_memberships=personnel_result.planning_unit_memberships,
            shifts=shift_result.shifts,
            assignments=roster_result.assignments,
            availability=roster_result.availability,
            demand_requirements=demand_result.demand_requirements,
            sunday_work_history=sunday_work_history_result.sunday_work_history,
            wishes=wish_result.wishes,
            monthly_work_accounts=monthly_work_account_result.monthly_work_accounts,
        )
