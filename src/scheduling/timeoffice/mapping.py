from src.scheduling.models.dataset import SchedulingDataset, StationMonthData
from src.scheduling.models.station import Station
from src.scheduling.timeoffice.models import TimeOfficeSourceData
from src.scheduling.timeoffice.settings import TimeOfficeSettings


class TimeOfficeMapper:
    """Map TimeOffice source data to canonical scheduling data.

    Boundary rules:
    - May know TimeOffice source meanings and mapping rules.
    - Must not query the database.
    - Must not read/write cache files.
    - Must not create solver variables or solver input.
    """

    def __init__(self, settings: TimeOfficeSettings):
        self._settings = settings

    def to_station_month_data(self, source_data: TimeOfficeSourceData) -> tuple[StationMonthData, ...]:
        """Map TimeOffice source data into one StationMonthData object per station.

        Current iteration: shallow placeholder.
        """
        print("[timeoffice] mapper.to_station_month_data")

        return tuple(
            StationMonthData(
                station=Station(
                    station_id=station_id,
                    source_planning_unit_id=station_id,
                ),
                period=source_data.period,
            )
            for station_id in source_data.station_ids
        )

    def combine_station_month_data(self, station_month_data: tuple[StationMonthData, ...]) -> SchedulingDataset:
        """Combine station-month data into one scheduling dataset.

        Current iteration: shallow concatenation without deduplication.
        """
        print("[timeoffice] mapper.combine_station_month_data")

        if not station_month_data:
            raise ValueError("Cannot combine empty station-month data.")

        period = station_month_data[0].period
        station_ids = tuple(data.station.station_id for data in station_month_data)

        effective_jump_pool_ids = tuple(
            station_id for station_id in station_ids if station_id in self._settings.jump_pool_station_ids
        )

        regular_station_ids = tuple(
            station_id for station_id in station_ids if station_id not in effective_jump_pool_ids
        )

        return SchedulingDataset(
            period=period,
            stations=tuple(data.station for data in station_month_data),
            regular_station_ids=regular_station_ids,
            jump_pool_station_ids=effective_jump_pool_ids,
            employees=tuple(employee for data in station_month_data for employee in data.employees),
            shifts=tuple(shift for data in station_month_data for shift in data.shifts),
            demand=tuple(demand for data in station_month_data for demand in data.demand),
            memberships=tuple(membership for data in station_month_data for membership in data.memberships),
            assignments=tuple(assignment for data in station_month_data for assignment in data.assignments),
            availability=tuple(item for data in station_month_data for item in data.availability),
            rules=tuple(rule for data in station_month_data for rule in data.rules),
            preferences=tuple(preference for data in station_month_data for preference in data.preferences),
        )
