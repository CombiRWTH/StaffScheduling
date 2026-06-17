from datetime import date as Date

from sqlalchemy import Connection, bindparam, text
from sqlalchemy.engine import RowMapping

from src.scheduling.models import (
    Assignment,
    AssignmentType,
    Availability,
    AvailabilityType,
    Employee,
    Plan,
    PlanningPeriod,
    SchedulingBaseModel,
)
from src.scheduling.timeoffice.facts import (
    TimeOfficeAvailabilityFact,
    TimeOfficeFacts,
    TimeOfficeShiftFact,
)
from src.scheduling.timeoffice.repositories.helpers import required, to_datetime


class RosterRepositoryResult(SchedulingBaseModel):
    assignments: tuple[Assignment, ...]
    availability: tuple[Availability, ...]


class TimeOfficeRosterRepository:
    """Reads hard roster facts from TimeOffice TPlanPersonalKommtGeht.

    This repository emits:
    - work rows as Assignment
    - absence rows as Availability

    Wishes/preferences are intentionally not emitted here yet, even though
    TPlanPersonalKommtGeht has `Wunschdienst`. They need a separate source
    analysis and a separate Preference model.
    """

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
        plans: tuple[Plan, ...],
        employees: tuple[Employee, ...],
        period: PlanningPeriod,
    ) -> RosterRepositoryResult:
        if not plans or not employees:
            return RosterRepositoryResult(assignments=(), availability=())

        selected_plan_ids = tuple(plan.plan_id for plan in plans)
        selected_planning_unit_ids = tuple(plan.planning_unit_id for plan in plans)
        employee_ids = tuple(employee.employee_id for employee in employees)

        rows = tuple(
            connection.execute(
                self._query(),
                {
                    "employee_ids": employee_ids,
                    "period_start": period.start,
                    "period_end": period.end,
                },
            )
            .mappings()
            .all()
        )

        return RosterRepositoryResult(
            assignments=self._map_assignments(
                rows=rows,
                selected_plan_ids=selected_plan_ids,
                selected_planning_unit_ids=selected_planning_unit_ids,
            ),
            availability=self._map_availability(rows=rows),
        )

    def _query(self):
        return text(
            """
            SELECT
                pkg.RefPlan AS plan_id,
                pkg.RefPersonal AS employee_id,
                pkg.Datum AS roster_date,
                pkg.lfdNr AS segment_number,

                pkg.RefDienste AS work_shift_id,
                work_d.KurzBez AS work_shift_code,

                pkg.RefgAbw AS global_absence_shift_id,
                global_absence_d.KurzBez AS global_absence_shift_code,

                pkg.RefDienstAbw AS absence_shift_id,
                absence_d.KurzBez AS absence_shift_code,

                pkg.RefPlanungseinheiten AS planning_unit_id,
                pkg.RefPeinheitOwner AS planning_unit_owner_id,

                pkg.Wunschdienst AS is_wish
            FROM TPlanPersonalKommtGeht pkg
            LEFT JOIN TDienste work_d
                ON work_d.Prim = pkg.RefDienste
            LEFT JOIN TDienste global_absence_d
                ON global_absence_d.Prim = pkg.RefgAbw
            LEFT JOIN TDienste absence_d
                ON absence_d.Prim = pkg.RefDienstAbw
            WHERE pkg.RefPersonal IN :employee_ids
                AND CONVERT(date, pkg.Datum) BETWEEN :period_start AND :period_end
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

    def _map_assignments(
        self,
        *,
        rows: tuple[RowMapping, ...],
        selected_plan_ids: tuple[int, ...],
        selected_planning_unit_ids: tuple[int, ...],
    ) -> tuple[Assignment, ...]:
        shift_facts = {int(fact.source_shift_id): fact for fact in self._facts.shift_facts}

        selected_plan_id_set = set(selected_plan_ids)
        selected_planning_unit_id_set = set(selected_planning_unit_ids)

        assignments_by_key: dict[
            tuple[int, Date, int, AssignmentType, int | None],
            Assignment,
        ] = {}
        unmapped_shift_ids: dict[int, int] = {}

        for row in rows:
            raw_shift_id = row["work_shift_id"]
            if raw_shift_id is None:
                continue

            shift_id = int(raw_shift_id)
            shift_fact = shift_facts.get(shift_id)

            if shift_fact is None:
                unmapped_shift_ids[shift_id] = unmapped_shift_ids.get(shift_id, 0) + 1
                continue

            self._validate_work_shift_code(row=row, fact=shift_fact)

            employee_id = self._employee_id(row)
            roster_date = required(
                to_datetime(row["roster_date"]),
                field_name="roster_date",
                context="TPlanPersonalKommtGeht",
            ).date()

            plan_id = self._optional_int(
                row["plan_id"],
                field_name="plan_id",
                context="TPlanPersonalKommtGeht",
            )

            planning_unit_id = self._optional_int(
                row["planning_unit_id"],
                field_name="planning_unit_id",
                context="TPlanPersonalKommtGeht",
            )

            assignment_type = self._assignment_type(
                plan_id=plan_id,
                planning_unit_id=planning_unit_id,
                selected_plan_ids=selected_plan_id_set,
                selected_planning_unit_ids=selected_planning_unit_id_set,
            )

            effective_planning_unit_id = planning_unit_id if assignment_type == AssignmentType.PLANNED else None

            assignment = Assignment(
                employee_id=employee_id,
                date=roster_date,
                shift_id=shift_id,
                assignment_type=assignment_type,
                planning_unit_id=effective_planning_unit_id,
            )

            key = (
                assignment.employee_id,
                assignment.date,
                assignment.shift_id,
                assignment.assignment_type,
                assignment.planning_unit_id,
            )
            assignments_by_key.setdefault(key, assignment)

        if unmapped_shift_ids:
            details = ", ".join(f"{shift_id} count={count}" for shift_id, count in sorted(unmapped_shift_ids.items()))
            raise ValueError(
                "Unmapped TimeOffice work shift ids found in "
                "TPlanPersonalKommtGeht. Add them to "
                "TIMEOFFICE_FACTS.scheduling_shift_facts or explicitly decide "
                f"to exclude them. Details: {details}."
            )

        return tuple(
            assignments_by_key[key]
            for key in sorted(
                assignments_by_key,
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                    item[3],
                    item[4] or -1,
                ),
            )
        )

    def _map_availability(
        self,
        *,
        rows: tuple[RowMapping, ...],
    ) -> tuple[Availability, ...]:
        availability_facts = {int(fact.source_shift_id): fact for fact in self._facts.availability_facts}

        availability_by_key: dict[
            tuple[int, Date, AvailabilityType],
            Availability,
        ] = {}
        unmapped_absence_ids: dict[int, int] = {}

        for row in rows:
            absence_shift_id = self._absence_shift_id(row)
            if absence_shift_id is None:
                continue

            fact = availability_facts.get(absence_shift_id)
            if fact is None:
                unmapped_absence_ids[absence_shift_id] = unmapped_absence_ids.get(absence_shift_id, 0) + 1
                continue

            self._validate_absence_code(row=row, fact=fact)

            employee_id = self._employee_id(row)
            roster_date = required(
                to_datetime(row["roster_date"]),
                field_name="roster_date",
                context="TPlanPersonalKommtGeht",
            ).date()

            availability = Availability(
                employee_id=employee_id,
                date=roster_date,
                availability_type=fact.availability_type,
            )

            key = (
                availability.employee_id,
                availability.date,
                availability.availability_type,
            )
            availability_by_key.setdefault(key, availability)

        if unmapped_absence_ids:
            details = ", ".join(
                f"{absence_id} count={count}" for absence_id, count in sorted(unmapped_absence_ids.items())
            )
            raise ValueError(
                "Unmapped TimeOffice absence shift ids found in "
                "TPlanPersonalKommtGeht. Add them to "
                f"TIMEOFFICE_FACTS.availability_facts. Details: {details}."
            )

        return tuple(
            availability_by_key[key]
            for key in sorted(
                availability_by_key,
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
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

    def _absence_shift_id(self, row: RowMapping) -> int | None:
        global_absence_shift_id = self._optional_int(
            row["global_absence_shift_id"],
            field_name="global_absence_shift_id",
            context="TPlanPersonalKommtGeht",
        )
        absence_shift_id = self._optional_int(
            row["absence_shift_id"],
            field_name="absence_shift_id",
            context="TPlanPersonalKommtGeht",
        )

        if global_absence_shift_id is None:
            return absence_shift_id

        if absence_shift_id is None:
            return global_absence_shift_id

        if global_absence_shift_id != absence_shift_id:
            raise ValueError(
                "Conflicting TimeOffice absence references in "
                "TPlanPersonalKommtGeht: "
                f"RefgAbw={global_absence_shift_id} "
                f"RefDienstAbw={absence_shift_id}."
            )

        return absence_shift_id

    def _validate_work_shift_code(
        self,
        *,
        row: RowMapping,
        fact: TimeOfficeShiftFact,
    ) -> None:
        actual_code = row["work_shift_code"]
        if actual_code is None:
            raise ValueError(
                f"Missing TDienste.KurzBez for TimeOffice work shift source_shift_id={fact.source_shift_id}."
            )

        actual = str(actual_code).strip()
        if actual != fact.expected_code:
            raise ValueError(
                "Unexpected TimeOffice work shift code: "
                f"source_shift_id={fact.source_shift_id} "
                f"expected={fact.expected_code!r} actual={actual!r}."
            )

    def _validate_absence_code(
        self,
        *,
        row: RowMapping,
        fact: TimeOfficeAvailabilityFact,
    ) -> None:
        actual_code = row["absence_shift_code"] or row["global_absence_shift_code"]
        if actual_code is None:
            raise ValueError(
                f"Missing TDienste.KurzBez for TimeOffice absence shift source_shift_id={fact.source_shift_id}."
            )

        actual = str(actual_code).strip()
        if actual != fact.expected_code:
            raise ValueError(
                "Unexpected TimeOffice absence code: "
                f"source_shift_id={fact.source_shift_id} "
                f"expected={fact.expected_code!r} actual={actual!r}."
            )

    def _employee_id(self, row: RowMapping) -> int:
        return int(
            required(
                row["employee_id"],
                field_name="employee_id",
                context="TPlanPersonalKommtGeht",
            )
        )

    def _optional_int(self, value: object, *, field_name: str, context: str) -> int | None:
        if value is None:
            return None

        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"Expected int or NULL for {field_name} in {context}, got {value!r}.")

        return value
