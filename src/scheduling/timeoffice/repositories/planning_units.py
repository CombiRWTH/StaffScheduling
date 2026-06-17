from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.models import Plan, PlanningPeriod, PlanningUnit, PlanningUnitKind, SchedulingBaseModel
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.repositories.types import SourceInt, TimeOfficeSourceRow


class _TimeOfficePlanningUnitRow(TimeOfficeSourceRow):
    planning_unit_id: SourceInt
    plan_id: SourceInt
    plan_planning_unit_id: SourceInt

    @model_validator(mode="after")
    def validate_plan_reference(self) -> Self:
        if self.plan_planning_unit_id != self.planning_unit_id:
            raise ValueError(
                "TimeOffice plan row references a different planning unit than the selected unit: "
                f"planning_unit_id={self.planning_unit_id} "
                f"plan_id={self.plan_id} "
                f"plan_planning_unit_id={self.plan_planning_unit_id}."
            )

        return self


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

        rows = self._fetch_rows(
            connection=connection,
            selected_planning_unit_ids=selected_planning_unit_ids,
            period=period,
        )

        self._validate_rows(
            requested_ids=selected_planning_unit_ids,
            rows=rows,
        )

        return PlanningUnitRepositoryResult(
            planning_units=self._map_planning_units(rows),
            plans=self._map_plans(rows),
        )

    def _fetch_rows(
        self,
        *,
        connection: Connection,
        selected_planning_unit_ids: tuple[int, ...],
        period: PlanningPeriod,
    ) -> tuple[_TimeOfficePlanningUnitRow, ...]:
        query = text(
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

        raw_rows = (
            connection.execute(
                query,
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

        return tuple(_TimeOfficePlanningUnitRow.model_validate(row) for row in raw_rows)

    def _validate_rows(self, *, requested_ids: tuple[int, ...], rows: tuple[_TimeOfficePlanningUnitRow, ...]) -> None:
        requested = set(requested_ids)
        returned_ids = [row.planning_unit_id for row in rows]

        missing = sorted(requested - set(returned_ids))
        if missing:
            raise ValueError(f"No selected TimeOffice target plan found for planning_unit_ids={missing}.")

        duplicates = self._duplicate_values(returned_ids)
        if duplicates:
            raise ValueError(f"Multiple selected TimeOffice target plans found for planning_unit_ids={duplicates}.")

    def _map_planning_units(self, rows: tuple[_TimeOfficePlanningUnitRow, ...]) -> tuple[PlanningUnit, ...]:
        return tuple(
            PlanningUnit(
                planning_unit_id=row.planning_unit_id,
                display_name=f"Planning Unit {row.planning_unit_id}",
                kind=self._facts.planning_unit_kind_map.get(
                    row.planning_unit_id,
                    PlanningUnitKind.STATION,
                ),
            )
            for row in rows
        )

    def _map_plans(self, rows: tuple[_TimeOfficePlanningUnitRow, ...]) -> tuple[Plan, ...]:
        return tuple(
            Plan(
                plan_id=row.plan_id,
                planning_unit_id=row.plan_planning_unit_id,
            )
            for row in rows
        )

    def _duplicate_values(self, values: list[int]) -> list[int]:
        seen: set[int] = set()
        duplicates: set[int] = set()

        for value in values:
            if value in seen:
                duplicates.add(value)
            seen.add(value)

        return sorted(duplicates)
