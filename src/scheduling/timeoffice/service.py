from src.scheduling.models import PlanningPeriod, SchedulingDataset
from src.scheduling.timeoffice.database import TimeOfficeDatabase
from src.scheduling.timeoffice.facts import TimeOfficeFacts


class TimeOfficeService:
    """Application-facing service for loading scheduling data from TimeOffice."""

    def __init__(
        self,
        *,
        facts: TimeOfficeFacts,
        database: TimeOfficeDatabase,
    ) -> None:
        self._facts = facts
        self._database = database

    def fetch_dataset(
        self,
        *,
        planning_unit_ids: tuple[int, ...],
        period: PlanningPeriod,
    ) -> SchedulingDataset:
        selected_planning_unit_ids = self._normalize_planning_unit_ids(planning_unit_ids)

        return self._database.fetch_dataset(
            selected_planning_unit_ids=selected_planning_unit_ids,
            period=period,
        )

    def _normalize_planning_unit_ids(
        self,
        planning_unit_ids: tuple[int, ...],
    ) -> tuple[int, ...]:
        normalized = tuple(dict.fromkeys(int(value) for value in planning_unit_ids))

        if not normalized:
            raise ValueError("At least one planning unit must be selected.")

        unknown_ids = sorted(
            planning_unit_id
            for planning_unit_id in normalized
            if planning_unit_id not in self._facts.planning_unit_kind_map
        )
        if unknown_ids:
            raise ValueError(
                "Unknown TimeOffice planning_unit_ids requested: "
                f"{unknown_ids}. Add them to TIMEOFFICE_FACTS.planning_unit_kind_map "
                "or fix the request."
            )

        return normalized
