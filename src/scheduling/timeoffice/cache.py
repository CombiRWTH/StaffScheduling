from pathlib import Path

from src.scheduling.models.core import PlanningPeriod
from src.scheduling.models.dataset import StationMonthData
from src.scheduling.timeoffice.models import CacheWriteResult
from src.scheduling.timeoffice.settings import TimeOfficeSettings


class TimeOfficeCache:
    """Local file cache for mapped scheduling data from TimeOffice.

    The cache stores canonical StationMonthData objects, not raw TimeOffice table
    dumps and not solver-specific objects.
    """

    STATION_MONTH_DATA_FILE = "station_month_data.json"

    def __init__(self, settings: TimeOfficeSettings):
        self._settings = settings

    def station_month_directory(self, station_id: int, period: PlanningPeriod) -> Path:
        """Return the cache directory for one station/month."""
        return self._settings.cache_root / str(station_id) / period.month_folder

    def station_month_data_path(self, station_id: int, period: PlanningPeriod) -> Path:
        """Return the station-month data JSON path."""
        return self.station_month_directory(station_id, period) / self.STATION_MONTH_DATA_FILE

    def read_many(self, station_ids: tuple[int, ...], period: PlanningPeriod) -> tuple[StationMonthData, ...]:
        """Read multiple station-month data objects from cache."""
        print("[timeoffice] cache.read_many")
        return tuple(self.read(station_id, period) for station_id in station_ids)

    def read(self, station_id: int, period: PlanningPeriod) -> StationMonthData:
        """Read one station-month data object from cache."""
        data_path = self.station_month_data_path(station_id, period)

        print(f"[timeoffice] cache.read station={station_id} path={data_path}")

        return StationMonthData.model_validate_json(data_path.read_text(encoding="utf-8"))

    def write_many(self, station_data: tuple[StationMonthData, ...]) -> tuple[CacheWriteResult, ...]:
        """Write multiple station-month data objects."""
        print("[timeoffice] cache.write_many")
        return tuple(self.write(data) for data in station_data)

    def write(self, data: StationMonthData) -> CacheWriteResult:
        """Write one station-month data object."""
        station_id = data.station.station_id
        cache_directory = self.station_month_directory(station_id, data.period)
        cache_directory.mkdir(parents=True, exist_ok=True)

        data_path = self.station_month_data_path(station_id, data.period)
        data_path.write_text(
            data.model_dump_json(indent=2),
            encoding="utf-8",
        )

        print(f"[timeoffice] cache.write station={station_id} path={data_path}")

        return CacheWriteResult(
            station_id=station_id,
            period=data.period,
            cache_directory=cache_directory,
        )
