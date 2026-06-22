from datetime import date, datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.domain import (
    Assignment,
    AssignmentType,
    Availability,
    AvailabilityType,
    Employee,
    Plan,
    PlanningMonth,
    SchedulingBaseModel,
)
from scheduling.timeoffice.facts import TimeOfficeFacts, TimeOfficeShiftFact
from scheduling.timeoffice.repositories.types import (
    CleanNullableText,
    SourceInt,
    SourceNullableInt,
    TimeOfficeSourceRow,
)


class _TimeOfficeRosterRow(TimeOfficeSourceRow):
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
                "Conflicting TimeOffice absence references in "
                "TPlanPersonalKommtGeht: "
                f"RefgAbw={self.global_absence_shift_id} "
                f"RefDienstAbw={self.absence_shift_id}."
            )

        return self


class RosterRepositoryResult(SchedulingBaseModel):
    assignments: tuple[Assignment, ...]
    availability: tuple[Availability, ...]


class TimeOfficeRosterRepository:
    """Reads hard roster facts from TimeOffice TPlanPersonalKommtGeht.

    This repository emits:
    - work rows as Assignment
    - absence rows as Availability

    Wishes/preferences are handled by TimeOfficeWishRepository. This repository
    intentionally keeps the existing roster import behavior and does not change
    semantics around Wunschdienst rows in this refactor.
    """

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
        plans: tuple[Plan, ...],
        employees: tuple[Employee, ...],
        planning_month: PlanningMonth,
    ) -> RosterRepositoryResult:
        if not plans or not employees:
            return RosterRepositoryResult(assignments=(), availability=())

        rows = self._fetch_rows(
            connection=connection,
            employees=employees,
            planning_month=planning_month,
        )

        selected_plan_ids = {plan.plan_id for plan in plans}
        selected_planning_unit_ids = {plan.planning_unit_id for plan in plans}

        return RosterRepositoryResult(
            assignments=self._map_assignments(
                rows=rows,
                selected_plan_ids=selected_plan_ids,
                selected_planning_unit_ids=selected_planning_unit_ids,
            ),
            availability=self._map_availability(rows=rows),
        )

    def _fetch_rows(
        self,
        *,
        connection: Connection,
        employees: tuple[Employee, ...],
        planning_month: PlanningMonth,
    ) -> tuple[_TimeOfficeRosterRow, ...]:
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
                    "employee_ids": tuple(employee.employee_id for employee in employees),
                    "start": planning_month.start,
                    "end": planning_month.end,
                },
            )
            .mappings()
            .all()
        )

        return tuple(_TimeOfficeRosterRow.model_validate(row) for row in raw_rows)

    def _map_assignments(
        self,
        *,
        rows: tuple[_TimeOfficeRosterRow, ...],
        selected_plan_ids: set[int],
        selected_planning_unit_ids: set[int],
    ) -> tuple[Assignment, ...]:
        assignments: list[Assignment] = []
        unmapped_shift_ids: dict[int, int] = {}

        for row in rows:
            if row.work_shift_id is None:
                continue

            shift_fact = self._facts.shift_facts_by_id.get(row.work_shift_id)

            if shift_fact is None:
                unmapped_shift_ids[row.work_shift_id] = unmapped_shift_ids.get(row.work_shift_id, 0) + 1
                continue

            assignments.append(
                self._map_assignment(
                    row=row,
                    shift_fact=shift_fact,
                    selected_plan_ids=selected_plan_ids,
                    selected_planning_unit_ids=selected_planning_unit_ids,
                )
            )

        if unmapped_shift_ids:
            details = ", ".join(f"{shift_id} count={count}" for shift_id, count in sorted(unmapped_shift_ids.items()))
            raise ValueError(
                "Unmapped TimeOffice work shift ids found in "
                "TPlanPersonalKommtGeht. Add them to "
                "TIMEOFFICE_FACTS.shift_facts_by_id or explicitly decide "
                f"to exclude them. Details: {details}."
            )

        return self._deduplicate_assignments(tuple(assignments))

    def _map_assignment(
        self,
        *,
        row: _TimeOfficeRosterRow,
        shift_fact: TimeOfficeShiftFact,
        selected_plan_ids: set[int],
        selected_planning_unit_ids: set[int],
    ) -> Assignment:
        if row.work_shift_id is None:
            raise ValueError(
                "Cannot map TimeOffice assignment without work_shift_id: "
                f"employee_id={row.employee_id} roster_date={row.roster_date}."
            )

        self._validate_work_shift_code(row=row, fact=shift_fact)

        assignment_type = self._assignment_type(
            plan_id=row.plan_id,
            planning_unit_id=row.planning_unit_id,
            selected_plan_ids=selected_plan_ids,
            selected_planning_unit_ids=selected_planning_unit_ids,
        )

        return Assignment(
            employee_id=row.employee_id,
            date=row.roster_date.date(),
            shift_id=row.work_shift_id,
            assignment_type=assignment_type,
            planning_unit_id=(row.planning_unit_id if assignment_type == AssignmentType.PLANNED else None),
        )

    def _deduplicate_assignments(self, assignments: tuple[Assignment, ...]) -> tuple[Assignment, ...]:
        assignments_by_key: dict[
            tuple[int, date, int, AssignmentType, int | None],
            Assignment,
        ] = {}

        for assignment in assignments:
            key = (
                assignment.employee_id,
                assignment.date,
                assignment.shift_id,
                assignment.assignment_type,
                assignment.planning_unit_id,
            )
            assignments_by_key.setdefault(key, assignment)

        return tuple(
            assignments_by_key[key]
            for key in sorted(
                assignments_by_key,
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                    item[3].value,
                    -1 if item[4] is None else item[4],
                ),
            )
        )

    def _map_availability(self, *, rows: tuple[_TimeOfficeRosterRow, ...]) -> tuple[Availability, ...]:
        availability: list[Availability] = []

        for row in rows:
            absence_shift_id = self._resolved_absence_shift_id(row)

            if absence_shift_id is None:
                continue

            availability.append(
                self._map_availability_row(
                    row=row,
                    absence_shift_id=absence_shift_id,
                )
            )

        return self._deduplicate_availability(tuple(availability))

    def _map_availability_row(self, *, row: _TimeOfficeRosterRow, absence_shift_id: int) -> Availability:
        if row.resolved_absence_code is None:
            raise ValueError(
                "Missing resolved absence code for TimeOffice roster row: "
                f"absence_shift_id={absence_shift_id} "
                f"employee_id={row.employee_id} "
                f"roster_date={row.roster_date}."
            )

        availability_type = self._facts.availability_type_by_absence_code.get(row.resolved_absence_code)

        if availability_type is None:
            raise ValueError(
                "Unmapped TimeOffice absence code: "
                f"absence_shift_id={absence_shift_id} "
                f"absence_code={row.resolved_absence_code!r}."
            )

        return Availability(
            employee_id=row.employee_id,
            date=row.roster_date.date(),
            availability_type=availability_type,
        )

    def _deduplicate_availability(self, availability: tuple[Availability, ...]) -> tuple[Availability, ...]:
        availability_by_key: dict[
            tuple[int, date, AvailabilityType],
            Availability,
        ] = {}

        for item in availability:
            key = (
                item.employee_id,
                item.date,
                item.availability_type,
            )
            availability_by_key.setdefault(key, item)

        return tuple(
            availability_by_key[key]
            for key in sorted(
                availability_by_key,
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2].value,
                ),
            )
        )

    def _assignment_type(
        self,
        *,
        plan_id: int | None,
        planning_unit_id: int | None,
        selected_plan_ids: set[int],
        selected_planning_unit_ids: set[int],
    ) -> AssignmentType:
        if plan_id in selected_plan_ids and planning_unit_id in selected_planning_unit_ids:
            return AssignmentType.PLANNED

        return AssignmentType.EXTERNAL

    def _resolved_absence_shift_id(self, row: _TimeOfficeRosterRow) -> int | None:
        if row.global_absence_shift_id is not None:
            return row.global_absence_shift_id

        if row.absence_shift_id is not None:
            return row.absence_shift_id

        return None

    def _validate_work_shift_code(self, *, row: _TimeOfficeRosterRow, fact: TimeOfficeShiftFact) -> None:
        if row.work_shift_id is None:
            raise ValueError("Cannot validate work shift code without work_shift_id.")

        if row.work_shift_code is None:
            raise ValueError(f"Missing TDienste.KurzBez for TimeOffice work shift source_shift_id={row.work_shift_id}.")

        if row.work_shift_code != fact.expected_code:
            raise ValueError(
                "Unexpected TimeOffice work shift code: "
                f"source_shift_id={row.work_shift_id} "
                f"expected={fact.expected_code!r} actual={row.work_shift_code!r}."
            )
