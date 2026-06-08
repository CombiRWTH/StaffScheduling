from src.scheduling.timeoffice.models import FetchStationsRequest, TimeOfficeSourceData
from src.scheduling.timeoffice.settings import TimeOfficeSettings


class TimeOfficeDatabase:
    """Read source data from the TimeOffice database.

    This class owns database access and SQL queries.
    """

    def __init__(self, settings: TimeOfficeSettings):
        self._settings = settings

    def read(self, request: FetchStationsRequest) -> TimeOfficeSourceData:
        """Read all source data needed to build StationMonthData.

        Current iteration: shallow placeholder.
        Later iterations: run optimized multi-station SQL queries.
        """
        print(
            "[timeoffice] database.read "
            f"stations={list(request.station_ids)} "
            f"period={request.period.start.isoformat()}..{request.period.end.isoformat()}"
        )

        return TimeOfficeSourceData(
            station_ids=request.station_ids,
            period=request.period,
        )
