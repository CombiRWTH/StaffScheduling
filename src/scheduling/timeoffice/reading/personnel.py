from datetime import datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.domain import PlanningMonth
from scheduling.timeoffice.reading.types import CleanNullableText, SourceInt, TimeOfficeSourceRow


class TimeOfficePlanPersonnelRow(TimeOfficeSourceRow):
    plan_id: SourceInt
    planning_unit_id: SourceInt
    employee_id: SourceInt


class TimeOfficeEmployeeRow(TimeOfficeSourceRow):
    employee_id: SourceInt
    employee_profession_id: SourceInt
    employee_profession_code: CleanNullableText = None
    first_name: CleanNullableText = None
    last_name: CleanNullableText = None


class TimeOfficePlanningUnitMembershipRow(TimeOfficeSourceRow):
    planning_unit_id: SourceInt
    employee_id: SourceInt
    membership_profession_id: SourceInt
    membership_profession_code: CleanNullableText = None
    valid_from: datetime
    valid_until: datetime | None = None
    is_home: bool
    is_replacement: bool

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.valid_until is not None and self.valid_until < self.valid_from:
            raise ValueError(
                "Invalid TimeOffice planning-unit membership interval: "
                f"planning_unit_id={self.planning_unit_id} "
                f"employee_id={self.employee_id} "
                f"valid_from={self.valid_from!r} "
                f"valid_until={self.valid_until!r}."
            )

        return self


class TimeOfficePersonnelReader:
    """Reads TimeOffice personnel source rows used for scheduling."""

    def read_plan_personnel_rows(
        self,
        *,
        connection: Connection,
        plan_ids: tuple[int, ...],
    ) -> tuple[TimeOfficePlanPersonnelRow, ...]:
        if not plan_ids:
            return ()

        query = text(
            """
            SELECT
                pp.RefPlan AS plan_id,
                p.RefPlanungseinheiten AS planning_unit_id,
                pp.RefPersonal AS employee_id
            FROM TPlanPersonal pp
            JOIN TPlan p
                ON p.Prim = pp.RefPlan
            WHERE pp.RefPlan IN :plan_ids
            ORDER BY
                p.RefPlanungseinheiten,
                pp.RefPlan,
                pp.RefPersonal
            """
        ).bindparams(bindparam("plan_ids", expanding=True))

        raw_rows = connection.execute(query, {"plan_ids": plan_ids}).mappings().all()

        return tuple(TimeOfficePlanPersonnelRow.model_validate(row) for row in raw_rows)

    def read_membership_rows(
        self,
        *,
        connection: Connection,
        planning_unit_ids: tuple[int, ...],
        planning_month: PlanningMonth,
    ) -> tuple[TimeOfficePlanningUnitMembershipRow, ...]:
        if not planning_unit_ids:
            return ()

        query = text(
            """
            SELECT
                pep.RefPlanungseinheiten AS planning_unit_id,
                pep.RefPersonal AS employee_id,
                pep.RefBerufe AS membership_profession_id,
                b.KurzBez AS membership_profession_code,
                pep.VonDat AS valid_from,
                pep.BisDat AS valid_until,
                pep.IstHeimat AS is_home,
                pep.IstVonErsatz AS is_replacement
            FROM TPlanungseinheitenPersonal pep
            LEFT JOIN TBerufe b
                ON b.Prim = pep.RefBerufe
            WHERE pep.RefPlanungseinheiten IN :planning_unit_ids
                AND CONVERT(date, pep.VonDat) <= :end
                AND (
                    pep.BisDat IS NULL
                    OR CONVERT(date, pep.BisDat) >= :start
                )
                AND ISNULL(pep.KeinEPlan, 0) = 0
            ORDER BY
                planning_unit_id,
                employee_id,
                valid_from,
                valid_until
            """
        ).bindparams(bindparam("planning_unit_ids", expanding=True))

        raw_rows = (
            connection.execute(
                query,
                {
                    "planning_unit_ids": planning_unit_ids,
                    "start": planning_month.start,
                    "end": planning_month.end,
                },
            )
            .mappings()
            .all()
        )

        return tuple(TimeOfficePlanningUnitMembershipRow.model_validate(row) for row in raw_rows)

    def read_employee_rows(
        self,
        *,
        connection: Connection,
        employee_ids: tuple[int, ...],
    ) -> tuple[TimeOfficeEmployeeRow, ...]:
        if not employee_ids:
            return ()

        query = text(
            """
            SELECT
                per.Prim AS employee_id,
                per.RefBerufe AS employee_profession_id,
                b.KurzBez AS employee_profession_code,
                per.Vorname AS first_name,
                per.Name AS last_name
            FROM TPersonal per
            LEFT JOIN TBerufe b
                ON b.Prim = per.RefBerufe
            WHERE per.Prim IN :employee_ids
            ORDER BY
                per.Name,
                per.Vorname,
                per.Prim
            """
        ).bindparams(bindparam("employee_ids", expanding=True))

        raw_rows = connection.execute(query, {"employee_ids": employee_ids}).mappings().all()

        rows = tuple(TimeOfficeEmployeeRow.model_validate(row) for row in raw_rows)
        self._validate_all_requested_employees_found(
            requested_employee_ids=employee_ids,
            rows=rows,
        )

        return rows

    def _validate_all_requested_employees_found(
        self,
        *,
        requested_employee_ids: tuple[int, ...],
        rows: tuple[TimeOfficeEmployeeRow, ...],
    ) -> None:
        returned_employee_ids = {row.employee_id for row in rows}
        missing_employee_ids = sorted(set(requested_employee_ids) - returned_employee_ids)

        if missing_employee_ids:
            raise ValueError(f"Missing TimeOffice employee master rows for employee_ids={missing_employee_ids}.")
