from pydantic import BaseModel, Field
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection

from src.scheduling.models.core import PlanningPeriod
from src.scheduling.models.station import Station
from src.scheduling.timeoffice.config import TimeOfficeConfig
from src.scheduling.timeoffice.models import FetchStationsRequest


class TimeOfficePlan(BaseModel):
    """TimeOffice monthly plan metadata for one station/planning unit."""

    station_id: int = Field(gt=0)
    source_plan_id: int = Field(gt=0)
    source_planning_unit_id: int = Field(gt=0)

    station_name: str | None = None

    status_id: int | None = None
    planning_interval_id: int | None = None

    period: PlanningPeriod


class PlanRepositoryResult(BaseModel):
    """Canonical output of reading TimeOffice plans."""

    plans: tuple[TimeOfficePlan, ...]
    stations: tuple[Station, ...]


class TimeOfficePlanRepository:
    """Read monthly TimeOffice plans and station metadata."""

    def __init__(self, config: TimeOfficeConfig):
        self._config = config

    def fetch(
        self,
        connection: Connection,
        request: FetchStationsRequest,
    ) -> PlanRepositoryResult:
        """Read monthly target plans for all requested stations."""
        query = text(
            """
            SELECT
                p.Prim AS source_plan_id,
                p.RefPlanungseinheiten AS source_planning_unit_id,
                p.RefPlanungseinheiten AS station_id,
                COALESCE(pe.Bezeichnung, pe.KurzBez) AS station_name,
                p.RefStati AS status_id,
                p.RefPlanungsIntervalle AS planning_interval_id
            FROM TPlan p
            LEFT JOIN TPlanungseinheiten pe
                ON pe.Prim = p.RefPlanungseinheiten
            WHERE p.RefPlanungseinheiten IN :station_ids
                AND p.VonDat = :period_start
                AND p.BisDat = :period_end
                AND p.RefPlanungsIntervalle = :planning_interval_id
                AND p.RefStati = :status_id
            """
        ).bindparams(bindparam("station_ids", expanding=True))

        rows = (
            connection.execute(
                query,
                {
                    "station_ids": request.station_ids,
                    "period_start": request.period.start,
                    "period_end": request.period.end,
                    "planning_interval_id": self._config.plan_selection.planning_interval_id,
                    "status_id": self._config.plan_selection.plan_status_id,
                },
            )
            .mappings()
            .all()
        )

        plans = tuple(
            TimeOfficePlan(
                station_id=row["station_id"],
                source_plan_id=row["source_plan_id"],
                source_planning_unit_id=row["source_planning_unit_id"],
                station_name=row["station_name"],
                status_id=row["status_id"],
                planning_interval_id=row["planning_interval_id"],
                period=request.period,
            )
            for row in rows
        )

        self._ensure_one_plan_per_requested_station(request, plans)

        stations = tuple(
            Station(
                station_id=plan.station_id,
                name=plan.station_name,
                source_planning_unit_id=plan.source_planning_unit_id,
            )
            for plan in plans
        )

        print(f"[timeoffice] database.repository.plans rows={len(plans)}")

        return PlanRepositoryResult(
            plans=plans,
            stations=stations,
        )

    def _ensure_one_plan_per_requested_station(
        self,
        request: FetchStationsRequest,
        plans: tuple[TimeOfficePlan, ...],
    ) -> None:
        """Ensure the query returned exactly one plan per requested station."""
        plans_by_station: dict[int, list[TimeOfficePlan]] = {station_id: [] for station_id in request.station_ids}

        for plan in plans:
            plans_by_station.setdefault(plan.station_id, []).append(plan)

        missing_station_ids = [
            station_id for station_id, station_plans in plans_by_station.items() if not station_plans
        ]

        if missing_station_ids:
            raise ValueError(
                "No monthly target TimeOffice plan found for station(s) "
                f"{missing_station_ids} and period "
                f"{request.period.start.isoformat()}..{request.period.end.isoformat()}."
            )

        ambiguous_station_ids = [
            station_id for station_id, station_plans in plans_by_station.items() if len(station_plans) > 1
        ]

        if ambiguous_station_ids:
            details = {
                station_id: [plan.source_plan_id for plan in station_plans]
                for station_id, station_plans in plans_by_station.items()
                if len(station_plans) > 1
            }

            raise ValueError(f"Multiple monthly target TimeOffice plans found for station(s): {details}")
