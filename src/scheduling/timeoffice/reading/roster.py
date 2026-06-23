from datetime import datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.domain import PlanningMonth
from scheduling.timeoffice.reading.types import CleanNullableText, SourceInt, SourceNullableInt, TimeOfficeSourceRow


class TimeOfficeRosterRow(TimeOfficeSourceRow):
    plan_id: SourceNullableInt = None
    employee_id: SourceInt
    roster_date: datetime

    work_shift_id: SourceNullableInt = None
    work_shift_code: CleanNullableText = None

    global_absence_shift_id: SourceNullableInt = None
    absence_shift_id: SourceNullableInt = None
    resolved_absence_shift_id: SourceNullableInt = None
    resolved_absence_code: CleanNullableText = None

    planning_unit_id: SourceNullableInt = None

    @model_validator(mode="after")
    def validate_row_kind(self) -> Self:
        has_work_shift = self.work_shift_id is not None
        has_absence = self.global_absence_shift_id is not None or self.absence_shift_id is not None

        if not has_work_shift and not has_absence:
            raise ValueError(
                "Invalid TimeOffice roster row: neither work shift nor absence is set "
                f"for employee_id={self.employee_id}, roster_date={self.roster_date}."
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
                "Conflicting TimeOffice absence references in TPlanPersonalKommtGeht: "
                f"RefgAbw={self.global_absence_shift_id} "
                f"RefDienstAbw={self.absence_shift_id}."
            )

        return self


class TimeOfficeRosterReader:
    """Reads TimeOffice roster source rows from TPlanPersonalKommtGeht."""

    def read_rows(
        self,
        *,
        connection: Connection,
        employee_ids: tuple[int, ...],
        planning_month: PlanningMonth,
    ) -> tuple[TimeOfficeRosterRow, ...]:
        if not employee_ids:
            return ()

        query = text(
            """
            SELECT
                pkg.RefPlan AS plan_id,
                pkg.RefPersonal AS employee_id,
                pkg.Datum AS roster_date,

                pkg.RefDienste AS work_shift_id,
                work_d.KurzBez AS work_shift_code,

                pkg.RefgAbw AS global_absence_shift_id,
                pkg.RefDienstAbw AS absence_shift_id,

                COALESCE(pkg.RefgAbw, pkg.RefDienstAbw) AS resolved_absence_shift_id,
                COALESCE(global_absence_d.KurzBez, absence_d.KurzBez) AS resolved_absence_code,

                pkg.RefPlanungseinheiten AS planning_unit_id
            FROM TPlanPersonalKommtGeht pkg
            LEFT JOIN TDienste work_d
                ON work_d.Prim = pkg.RefDienste
            LEFT JOIN TDienste global_absence_d
                ON global_absence_d.Prim = pkg.RefgAbw
            LEFT JOIN TDienste absence_d
                ON absence_d.Prim = pkg.RefDienstAbw
            WHERE pkg.RefPersonal IN :employee_ids
                AND CONVERT(date, pkg.Datum) BETWEEN :start AND :end
                AND (
                    pkg.RefDienste IS NOT NULL
                    OR pkg.RefgAbw IS NOT NULL
                    OR pkg.RefDienstAbw IS NOT NULL
                )
            ORDER BY
                pkg.RefPersonal,
                pkg.Datum,
                pkg.RefPlan,
                pkg.lfdNr
            """
        ).bindparams(bindparam("employee_ids", expanding=True))

        raw_rows = (
            connection.execute(
                query,
                {
                    "employee_ids": employee_ids,
                    "start": planning_month.start,
                    "end": planning_month.end,
                },
            )
            .mappings()
            .all()
        )

        return tuple(TimeOfficeRosterRow.model_validate(row) for row in raw_rows)
