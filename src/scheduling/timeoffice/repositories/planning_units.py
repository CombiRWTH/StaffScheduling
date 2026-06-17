from sqlalchemy import Connection, bindparam, text
from sqlalchemy.engine import RowMapping

from src.scheduling.models import (
    Plan,
    PlanningPeriod,
    PlanningUnit,
    PlanningUnitKind,
    SchedulingBaseModel,
)
from src.scheduling.timeoffice.facts import TimeOfficeFacts
from src.scheduling.timeoffice.repositories.helpers import required


class PlanningUnitRepositoryResult(SchedulingBaseModel):
    planning_units: tuple[PlanningUnit, ...]
    plans: tuple[Plan, ...]


class TimeOfficePlanningUnitRepository:
    """Reads selected TimeOffice planning units and their concrete plans."""

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
        selected_planning_unit_ids: tuple[int, ...],
        period: PlanningPeriod,
    ) -> PlanningUnitRepositoryResult:
        if not selected_planning_unit_ids:
            return PlanningUnitRepositoryResult(planning_units=(), plans=())

        rows = tuple(
            connection.execute(
                self._query(),
                {
                    "planning_unit_ids": selected_planning_unit_ids,
                    "period_start": period.start,
                    "period_end": period.end,
                    "planning_interval_id": self._facts.monthly_planning_interval_id,
                    "planning_status_id": self._facts.target_planning_status_id,
                },
            )
            .mappings()
            .all()
        )

        planning_units = tuple(self._map_planning_unit(row) for row in rows)
        plans = tuple(self._map_plan(row) for row in rows)

        self._validate_result(
            requested_ids=selected_planning_unit_ids,
            planning_units=planning_units,
            plans=plans,
        )

        return PlanningUnitRepositoryResult(
            planning_units=planning_units,
            plans=plans,
        )

    def _query(self):
        return text(
            """
            SELECT
                pe.Prim AS planning_unit_id,
                p.Prim AS plan_id,
                p.RefPlanungseinheiten AS plan_planning_unit_id
            FROM TPlanungseinheiten pe
            JOIN TPlan p
                ON p.RefPlanungseinheiten = pe.Prim
            WHERE pe.Prim IN :planning_unit_ids
                AND p.RefPlanungsIntervalle = :planning_interval_id
                AND p.RefStati = :planning_status_id
                AND CONVERT(date, p.VonDat) = :period_start
                AND CONVERT(date, p.BisDat) = :period_end
            ORDER BY pe.Prim
            """
        ).bindparams(bindparam("planning_unit_ids", expanding=True))

    def _map_planning_unit(self, row: RowMapping) -> PlanningUnit:
        planning_unit_id = int(
            required(
                row["planning_unit_id"],
                field_name="planning_unit_id",
                context="TPlanungseinheiten",
            )
        )

        return PlanningUnit(
            planning_unit_id=planning_unit_id,
            display_name=f"Planning Unit {planning_unit_id}",
            kind=self._facts.planning_unit_kind_map.get(
                planning_unit_id,
                PlanningUnitKind.STATION,
            ),
        )

    def _map_plan(self, row: RowMapping) -> Plan:
        return Plan(
            plan_id=int(required(row["plan_id"], field_name="plan_id", context="TPlan")),
            planning_unit_id=int(
                required(
                    row["plan_planning_unit_id"],
                    field_name="plan_planning_unit_id",
                    context="TPlan",
                )
            ),
        )

    def _validate_result(
        self,
        *,
        requested_ids: tuple[int, ...],
        planning_units: tuple[PlanningUnit, ...],
        plans: tuple[Plan, ...],
    ) -> None:
        requested = set(requested_ids)
        returned_units = [unit.planning_unit_id for unit in planning_units]
        returned_plans = [plan.planning_unit_id for plan in plans]

        missing = sorted(requested - set(returned_units))
        if missing:
            raise ValueError(f"No selected TimeOffice target plan found for planning_unit_ids={missing}.")

        duplicates = sorted(
            {planning_unit_id for planning_unit_id in returned_units if returned_units.count(planning_unit_id) > 1}
        )
        if duplicates:
            raise ValueError(f"Multiple selected TimeOffice target plans found for planning_unit_ids={duplicates}.")

        if set(returned_units) != set(returned_plans):
            raise ValueError(
                "Planning units and plans do not match: "
                f"planning_units={sorted(returned_units)} "
                f"plans={sorted(returned_plans)}."
            )
