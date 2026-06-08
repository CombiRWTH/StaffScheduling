from sqlalchemy import URL, bindparam, create_engine, text
from sqlalchemy.engine import Engine

from src.scheduling.timeoffice.constants import TimeOfficePlanningInterval, TimeOfficePlanStatus
from src.scheduling.timeoffice.models import FetchStationsRequest, TimeOfficeSourceData
from src.scheduling.timeoffice.settings import TimeOfficeSettings
from src.scheduling.timeoffice.source_models import TimeOfficePlanEmployeeSource, TimeOfficePlanSource


class TimeOfficeDatabase:
    """Read source data from the TimeOffice database.

    This class owns database access and SQL queries.
    """

    def __init__(self, settings: TimeOfficeSettings):
        self._settings = settings
        self._engine: Engine | None = None

    def _get_engine(self) -> Engine:
        """Create or return the TimeOffice database engine."""
        if self._engine is None:
            self._engine = create_engine(self._database_url())

        return self._engine

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

    def read(self, request: FetchStationsRequest) -> TimeOfficeSourceData:
        """Read all source data needed to build StationMonthData."""
        print(
            "[timeoffice] database.read "
            f"stations={list(request.station_ids)} "
            f"period={request.period.start.isoformat()}..{request.period.end.isoformat()}"
        )

        plans = self._read_plans(request)
        plan_employees = self._read_plan_employees(plans)

        return TimeOfficeSourceData(
            station_ids=request.station_ids,
            period=request.period,
            plans=plans,
            plan_employees=plan_employees,
        )

    def _read_plans(self, request: FetchStationsRequest) -> tuple[TimeOfficePlanSource, ...]:
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

        with self._get_engine().connect() as connection:
            rows = (
                connection.execute(
                    query,
                    {
                        "station_ids": request.station_ids,
                        "period_start": request.period.start,
                        "period_end": request.period.end,
                        "planning_interval_id": TimeOfficePlanningInterval.MONTHLY,
                        "status_id": TimeOfficePlanStatus.TARGET_PLANNING,
                    },
                )
                .mappings()
                .all()
            )

        plans = tuple(
            TimeOfficePlanSource(
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

        print(f"[timeoffice] database.read_plans rows={len(plans)}")

        return plans

    def _ensure_one_plan_per_requested_station(
        self, request: FetchStationsRequest, plans: tuple[TimeOfficePlanSource, ...]
    ) -> None:
        """Ensure the plan query returned exactly one plan per requested station."""
        plans_by_station: dict[int, list[TimeOfficePlanSource]] = {station_id: [] for station_id in request.station_ids}

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

    def _read_plan_employees(
        self,
        plans: tuple[TimeOfficePlanSource, ...],
    ) -> tuple[TimeOfficePlanEmployeeSource, ...]:
        """Read employees assigned to the selected monthly TimeOffice plans."""
        plan_ids = tuple(plan.source_plan_id for plan in plans)

        query = text(
            """
            SELECT
                pp.Prim AS source_plan_employee_id,
                pp.RefPlan AS source_plan_id,
                tp.RefPlanungseinheiten AS station_id,
                pp.RefPersonal AS employee_id,

                p.PersNr AS personnel_number,
                p.Vorname AS first_name,
                p.Name AS last_name,
                p.KurzName AS short_name,

                pp.RefBerufe AS source_profession_id,
                pp.VonDat AS valid_from,
                pp.BisDat AS valid_until,
                pp.IstVonErsatz AS is_substitute
            FROM TPlanPersonal pp
            JOIN TPlan tp
                ON tp.Prim = pp.RefPlan
            JOIN TPersonal p
                ON p.Prim = pp.RefPersonal
            WHERE pp.RefPlan IN :plan_ids
            """
        ).bindparams(bindparam("plan_ids", expanding=True))

        with self._get_engine().connect() as connection:
            rows = connection.execute(query, {"plan_ids": plan_ids}).mappings().all()

        plan_employees = tuple(
            TimeOfficePlanEmployeeSource(
                source_plan_employee_id=row["source_plan_employee_id"],
                source_plan_id=row["source_plan_id"],
                station_id=row["station_id"],
                employee_id=row["employee_id"],
                personnel_number=row["personnel_number"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                short_name=row["short_name"],
                source_profession_id=row["source_profession_id"],
                valid_from=None if row["valid_from"] is None else row["valid_from"].date(),
                valid_until=None if row["valid_until"] is None else row["valid_until"].date(),
                is_substitute=None if row["is_substitute"] is None else bool(row["is_substitute"]),
            )
            for row in rows
        )

        print(f"[timeoffice] database.read_plan_employees rows={len(plan_employees)}")

        return plan_employees
