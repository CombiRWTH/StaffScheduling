from datetime import datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.domain import PlanningMonth
from scheduling.timeoffice.reading.types import CleanNullableText, SourceInt, SourceNullableInt, TimeOfficeSourceRow


class TimeOfficeWishRow(TimeOfficeSourceRow):
    employee_id: SourceInt
    wish_date: datetime
    plan_id: SourceInt
    planning_unit_id: SourceInt

    work_shift_id: SourceNullableInt = None
    work_shift_code: CleanNullableText = None
    work_shift_name: CleanNullableText = None

    global_absence_shift_id: SourceNullableInt = None
    global_absence_shift_code: CleanNullableText = None
    global_absence_shift_name: CleanNullableText = None

    absence_shift_id: SourceNullableInt = None
    absence_shift_code: CleanNullableText = None
    absence_shift_name: CleanNullableText = None

    resolved_absence_shift_id: SourceNullableInt = None
    resolved_absence_code: CleanNullableText = None
    resolved_absence_name: CleanNullableText = None

    @model_validator(mode="after")
    def validate_row_kind(self) -> Self:
        has_work_shift = self.work_shift_id is not None
        has_absence = self.global_absence_shift_id is not None or self.absence_shift_id is not None

        if has_work_shift and has_absence:
            raise ValueError(
                "Ambiguous TimeOffice wish row: both work shift and absence are set "
                f"for employee_id={self.employee_id}, wish_date={self.wish_date}."
            )

        if not has_work_shift and not has_absence:
            raise ValueError(
                "Invalid TimeOffice wish row: neither work shift nor absence is set "
                f"for employee_id={self.employee_id}, wish_date={self.wish_date}."
            )

        return self

    @model_validator(mode="after")
    def validate_absence_references(self) -> Self:
        if (
            self.global_absence_shift_id is not None
            and self.absence_shift_id is not None
            and self.global_absence_shift_id != self.absence_shift_id
        ):
            raise ValueError(
                "Conflicting TimeOffice wish absence references in TPlanPersonalKommtGeht: "
                f"RefgAbw={self.global_absence_shift_id} "
                f"RefDienstAbw={self.absence_shift_id}."
            )

        return self


class TimeOfficeWishReader:
    """Reads employee wish source rows from TimeOffice."""

    def read_rows(
        self,
        *,
        connection: Connection,
        plan_ids: tuple[int, ...],
        planning_unit_ids: tuple[int, ...],
        employee_ids: tuple[int, ...],
        planning_month: PlanningMonth,
    ) -> tuple[TimeOfficeWishRow, ...]:
        if not plan_ids or not planning_unit_ids or not employee_ids:
            return ()

        query = text(
            """
            SELECT
                pkg.RefPersonal AS employee_id,
                pkg.Datum AS wish_date,
                pkg.RefPlan AS plan_id,
                pkg.RefPlanungseinheiten AS planning_unit_id,

                pkg.RefDienste AS work_shift_id,
                work_d.KurzBez AS work_shift_code,
                work_d.Bezeichnung AS work_shift_name,

                pkg.RefgAbw AS global_absence_shift_id,
                global_absence_d.KurzBez AS global_absence_shift_code,
                global_absence_d.Bezeichnung AS global_absence_shift_name,

                pkg.RefDienstAbw AS absence_shift_id,
                absence_d.KurzBez AS absence_shift_code,
                absence_d.Bezeichnung AS absence_shift_name,

                COALESCE(pkg.RefgAbw, pkg.RefDienstAbw) AS resolved_absence_shift_id,
                COALESCE(global_absence_d.KurzBez, absence_d.KurzBez) AS resolved_absence_code,
                COALESCE(global_absence_d.Bezeichnung, absence_d.Bezeichnung) AS resolved_absence_name
            FROM TPlanPersonalKommtGeht pkg
            LEFT JOIN TDienste work_d
                ON work_d.Prim = pkg.RefDienste
            LEFT JOIN TDienste global_absence_d
                ON global_absence_d.Prim = pkg.RefgAbw
            LEFT JOIN TDienste absence_d
                ON absence_d.Prim = pkg.RefDienstAbw
            WHERE pkg.RefPersonal IN :employee_ids
                AND pkg.RefPlan IN :plan_ids
                AND pkg.RefPlanungseinheiten IN :planning_unit_ids
                AND CONVERT(date, pkg.Datum) BETWEEN :start AND :end
                AND ISNULL(pkg.Wunschdienst, 0) <> 0
                AND (
                    pkg.RefDienste IS NOT NULL
                    OR pkg.RefgAbw IS NOT NULL
                    OR pkg.RefDienstAbw IS NOT NULL
                )
            ORDER BY
                pkg.RefPersonal,
                pkg.Datum,
                pkg.RefPlan,
                pkg.RefPlanungseinheiten,
                pkg.RefDienste,
                pkg.RefgAbw,
                pkg.RefDienstAbw
            """
        ).bindparams(
            bindparam("employee_ids", expanding=True),
            bindparam("plan_ids", expanding=True),
            bindparam("planning_unit_ids", expanding=True),
        )

        raw_rows = (
            connection.execute(
                query,
                {
                    "plan_ids": plan_ids,
                    "planning_unit_ids": planning_unit_ids,
                    "employee_ids": employee_ids,
                    "start": planning_month.start,
                    "end": planning_month.end,
                },
            )
            .mappings()
            .all()
        )

        return tuple(TimeOfficeWishRow.model_validate(row) for row in raw_rows)
