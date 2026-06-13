from sqlalchemy import URL, create_engine
from sqlalchemy.engine import Engine

from src.scheduling.models.dataset import SchedulingDataset
from src.scheduling.timeoffice.config import TIMEOFFICE_CONFIG, TimeOfficeConfig
from src.scheduling.timeoffice.models import FetchStationsRequest
from src.scheduling.timeoffice.repositories.employees import TimeOfficeEmployeeRepository
from src.scheduling.timeoffice.repositories.plans import TimeOfficePlanRepository
from src.scheduling.timeoffice.repositories.shifts import TimeOfficeShiftRepository
from src.scheduling.timeoffice.settings import TimeOfficeSettings


class TimeOfficeDatabase:
    """Read TimeOffice data and build the canonical scheduling dataset.

    This class owns the database connection and explicit repository orchestration.
    Repositories own SQL access, source-local validation, and mapping to canonical
    scheduling models.
    """

    def __init__(
        self,
        settings: TimeOfficeSettings,
        config: TimeOfficeConfig = TIMEOFFICE_CONFIG,
    ):
        self._settings = settings
        self._config = config
        self._engine: Engine = create_engine(self._database_url())

        self._plans = TimeOfficePlanRepository(config)
        self._employees = TimeOfficeEmployeeRepository()
        self._shifts = TimeOfficeShiftRepository(config)

    def _database_url(self) -> URL:
        """Build the SQLAlchemy URL for the TimeOffice SQL Server database."""
        query: dict[str, str] = {
            "driver": self._settings.db_driver,
            "TrustServerCertificate": "yes",
        }

        return URL.create(
            drivername="mssql+pyodbc",
            username=self._settings.db_user,
            password=self._settings.db_password.get_secret_value(),
            host=self._settings.db_server,
            database=self._settings.db_name,
            query=query,
        )

    def read(self, request: FetchStationsRequest) -> SchedulingDataset:
        """Read and map TimeOffice data into the canonical scheduling dataset."""
        print(
            "[timeoffice] database.read "
            f"stations={list(request.station_ids)} "
            f"period={request.period.start.isoformat()}..{request.period.end.isoformat()}"
        )

        with self._engine.connect() as connection:
            plan_result = self._plans.fetch(connection, request)
            employee_result = self._employees.fetch(connection, plan_result.plans)
            shift_result = self._shifts.fetch(connection)

        return SchedulingDataset(
            period=request.period,
            stations=plan_result.stations,
            regular_station_ids=self._config.regular_station_ids_for(request.station_ids),
            jump_pool_station_ids=self._config.jump_pool_station_ids_for(request.station_ids),
            employees=employee_result.employees,
            shifts=shift_result.shifts,
            demand=(),
            memberships=employee_result.memberships,
            assignments=(),
            availability=(),
            rules=(),
            preferences=(),
        )
