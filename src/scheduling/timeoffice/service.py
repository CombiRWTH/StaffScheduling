from src.scheduling.models.dataset import SchedulingDataset, StationMonthData
from src.scheduling.timeoffice.cache import TimeOfficeCache
from src.scheduling.timeoffice.database import TimeOfficeDatabase
from src.scheduling.timeoffice.mapping import TimeOfficeMapper
from src.scheduling.timeoffice.models import FetchStationsRequest
from src.scheduling.timeoffice.settings import TimeOfficeSettings


class TimeOfficeService:
    """Public facade for TimeOffice data transfer."""

    def __init__(
        self,
        settings: TimeOfficeSettings,
        database: TimeOfficeDatabase,
        mapper: TimeOfficeMapper,
        cache: TimeOfficeCache,
    ):
        self._settings = settings
        self._database = database
        self._mapper = mapper
        self._cache = cache

    def fetch(self, request: FetchStationsRequest) -> SchedulingDataset:
        """Provide scheduling data for the requested TimeOffice stations.

        If request.use_cache is true, cached StationMonthData is attempted first.
        On cache miss or invalid cache data, the service falls back to database.

        If settings.enable_cache is true, database-derived StationMonthData is
        written to cache for debugging and validation.
        """
        print(
            "[timeoffice] service.fetch "
            f"stations={list(request.station_ids)} "
            f"period={request.period.start.isoformat()}..{request.period.end.isoformat()} "
            f"use_cache={request.use_cache} "
            f"enable_cache={self._settings.enable_cache}"
        )

        station_month_data = self._get_station_month_data(request)

        return self._mapper.combine_station_month_data(station_month_data=station_month_data)

    def _get_station_month_data(self, request: FetchStationsRequest) -> tuple[StationMonthData, ...]:
        """Load station-month data from cache or database according to policy."""
        if request.use_cache:
            try:
                return self._cache.read_many(
                    station_ids=request.station_ids,
                    period=request.period,
                )
            except Exception as error:
                print(
                    f"[timeoffice] cache unavailable; falling back to database reason={type(error).__name__}: {error}"
                )

        source_data = self._database.read(request)
        station_month_data = self._mapper.to_station_month_data(source_data)

        if self._settings.enable_cache:
            self._cache.write_many(station_month_data)

        return station_month_data


def create_timeoffice_service(settings: TimeOfficeSettings | None = None) -> TimeOfficeService:
    """Create the default TimeOffice service."""
    settings = settings or TimeOfficeSettings()

    return TimeOfficeService(
        settings=settings,
        database=TimeOfficeDatabase(settings),
        mapper=TimeOfficeMapper(settings),
        cache=TimeOfficeCache(settings),
    )
