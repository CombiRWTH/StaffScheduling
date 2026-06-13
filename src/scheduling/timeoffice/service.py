from src.scheduling.models.dataset import SchedulingDataset
from src.scheduling.timeoffice.config import TIMEOFFICE_CONFIG, TimeOfficeConfig
from src.scheduling.timeoffice.database import TimeOfficeDatabase
from src.scheduling.timeoffice.models import FetchStationsRequest
from src.scheduling.timeoffice.settings import TimeOfficeSettings, load_settings


class TimeOfficeService:
    """Public facade for TimeOffice data transfer."""

    def __init__(
        self,
        settings: TimeOfficeSettings,
        database: TimeOfficeDatabase,
    ):
        self._settings = settings
        self._database = database

    def fetch(self, request: FetchStationsRequest) -> SchedulingDataset:
        """Provide scheduling data for the requested TimeOffice stations."""
        print(
            "[timeoffice] service.fetch "
            f"stations={list(request.station_ids)} "
            f"period={request.period.start.isoformat()}..{request.period.end.isoformat()}"
        )

        return self._database.read(request)


def create_timeoffice_service(
    settings: TimeOfficeSettings | None = None,
    config: TimeOfficeConfig = TIMEOFFICE_CONFIG,
) -> TimeOfficeService:
    """Create the default TimeOffice service."""
    settings = settings or load_settings()

    return TimeOfficeService(
        settings=settings,
        database=TimeOfficeDatabase(settings, config),
    )
