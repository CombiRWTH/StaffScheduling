from datetime import date as Date
from datetime import datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.domain import Employee, Plan, PlanningMonth, SchedulingBaseModel, Shift, Wish, WishKind
from scheduling.timeoffice.facts import TimeOfficeFacts, TimeOfficeShiftFact
from scheduling.timeoffice.repositories.types import (
    CleanNullableText,
    SourceInt,
    SourceNullableInt,
    TimeOfficeSourceRow,
)


class _TimeOfficeWishRow(TimeOfficeSourceRow):
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
                "Conflicting TimeOffice wish absence references in "
                "TPlanPersonalKommtGeht: "
                f"RefgAbw={self.global_absence_shift_id} "
                f"RefDienstAbw={self.absence_shift_id}."
            )

        return self


class TimeOfficeWishRepositoryResult(SchedulingBaseModel):
    wishes: tuple[Wish, ...]


class TimeOfficeWishRepository:
    """Reads employee wishes from TimeOffice TPlanPersonalKommtGeht.

    Source rule:
    - only rows with Wunschdienst != 0
    - work shift rows become SHIFT wishes
    - mapped absence rows become FREE_DAY wishes for now

    TPersonalAntraege is intentionally not used yet because source validation did
    not show usable request workflow rows for the selected planning context.
    """

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
        plans: tuple[Plan, ...],
        employees: tuple[Employee, ...],
        shifts: tuple[Shift, ...],
        planning_month: PlanningMonth,
    ) -> TimeOfficeWishRepositoryResult:
        if not plans or not employees:
            return TimeOfficeWishRepositoryResult(wishes=())

        rows = self._fetch_rows(
            connection=connection,
            plans=plans,
            employees=employees,
            planning_month=planning_month,
        )

        wishes = self._map_wishes(rows=rows, shifts=shifts)

        return TimeOfficeWishRepositoryResult(wishes=self._deduplicate_wishes(wishes))

    def _fetch_rows(
        self,
        *,
        connection: Connection,
        plans: tuple[Plan, ...],
        employees: tuple[Employee, ...],
        planning_month: PlanningMonth,
    ) -> tuple[_TimeOfficeWishRow, ...]:
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

        raw_rows = tuple(
            connection.execute(
                query,
                {
                    "plan_ids": tuple(plan.plan_id for plan in plans),
                    "planning_unit_ids": tuple(plan.planning_unit_id for plan in plans),
                    "employee_ids": tuple(employee.employee_id for employee in employees),
                    "start": planning_month.start,
                    "end": planning_month.end,
                },
            )
            .mappings()
            .all()
        )

        return tuple(_TimeOfficeWishRow.model_validate(row) for row in raw_rows)

    def _map_wishes(self, *, rows: tuple[_TimeOfficeWishRow, ...], shifts: tuple[Shift, ...]) -> tuple[Wish, ...]:
        known_shift_ids = {shift.shift_id for shift in shifts}

        return tuple(
            self._map_wish(
                row=row,
                known_shift_ids=known_shift_ids,
            )
            for row in rows
        )

    def _map_wish(self, *, row: _TimeOfficeWishRow, known_shift_ids: set[int]) -> Wish:
        if row.work_shift_id is not None:
            return self._map_shift_wish(row=row, known_shift_ids=known_shift_ids)

        return self._map_absence_wish(row=row)

    def _map_shift_wish(self, *, row: _TimeOfficeWishRow, known_shift_ids: set[int]) -> Wish:
        if row.work_shift_id is None:
            raise ValueError("Cannot map shift wish without work_shift_id.")

        fact = self._facts.shift_facts_by_id.get(row.work_shift_id)
        if fact is None or row.work_shift_id not in known_shift_ids:
            raise ValueError(
                "Unmapped TimeOffice wish work shift id found in "
                "TPlanPersonalKommtGeht. Add it to TIMEOFFICE_FACTS.shift_facts_by_id "
                f"or explicitly decide to exclude it. Details: shift_id={row.work_shift_id}."
            )

        self._validate_work_shift_code(row=row, fact=fact)

        return Wish(
            employee_id=row.employee_id,
            planning_unit_id=row.planning_unit_id,
            date=row.wish_date.date(),
            kind=WishKind.SHIFT,
            shift_id=row.work_shift_id,
        )

    def _map_absence_wish(self, *, row: _TimeOfficeWishRow) -> Wish:
        absence_shift_id = self._resolved_absence_shift_id(row)

        if row.resolved_absence_code is None:
            raise ValueError(
                "Missing resolved absence code for TimeOffice wish row: "
                f"absence_shift_id={absence_shift_id} "
                f"employee_id={row.employee_id} "
                f"wish_date={row.wish_date}."
            )

        wish_kind = self._facts.wish_kind_by_absence_code.get(row.resolved_absence_code)
        if wish_kind is None:
            raise ValueError(
                "Unmapped TimeOffice wish absence code: "
                f"absence_shift_id={absence_shift_id} "
                f"absence_code={row.resolved_absence_code!r} "
                f"absence_name={row.resolved_absence_name!r}."
            )

        return Wish(
            employee_id=row.employee_id,
            planning_unit_id=row.planning_unit_id,
            date=row.wish_date.date(),
            kind=wish_kind,
        )

    def _validate_work_shift_code(self, *, row: _TimeOfficeWishRow, fact: TimeOfficeShiftFact) -> None:
        if row.work_shift_code is None:
            raise ValueError(
                f"Missing TDienste.KurzBez for TimeOffice wish work shift source_shift_id={fact.source_shift_id}."
            )

        if row.work_shift_code != fact.expected_code:
            raise ValueError(
                "Unexpected TimeOffice wish work shift code: "
                f"source_shift_id={fact.source_shift_id} "
                f"expected={fact.expected_code!r} actual={row.work_shift_code!r}."
            )

    def _resolved_absence_shift_id(self, row: _TimeOfficeWishRow) -> int:
        if row.global_absence_shift_id is not None:
            return row.global_absence_shift_id

        if row.absence_shift_id is not None:
            return row.absence_shift_id

        raise ValueError(
            "Invalid TimeOffice wish row after source-row validation: "
            f"missing absence shift id for employee_id={row.employee_id}, "
            f"wish_date={row.wish_date}."
        )

    def _deduplicate_wishes(self, wishes: tuple[Wish, ...]) -> tuple[Wish, ...]:
        wishes_by_key: dict[tuple[int, int, Date, WishKind, int | None], Wish] = {}

        for wish in wishes:
            key = (
                wish.employee_id,
                wish.planning_unit_id,
                wish.date,
                wish.kind,
                wish.shift_id,
            )
            wishes_by_key.setdefault(key, wish)

        return tuple(
            wishes_by_key[key]
            for key in sorted(
                wishes_by_key,
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4] or -1,
                ),
            )
        )
