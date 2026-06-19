from datetime import datetime
from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.domain import (
    Capability,
    Employee,
    Plan,
    PlanningPeriod,
    PlanningUnitMembership,
    PlanParticipant,
    SchedulingBaseModel,
    StaffLevel,
)
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.repositories.types import CleanNullableText, SourceInt, TimeOfficeSourceRow


class _TimeOfficePlanPersonnelRow(TimeOfficeSourceRow):
    plan_id: SourceInt
    planning_unit_id: SourceInt
    employee_id: SourceInt
    employee_profession_id: SourceInt
    first_name: CleanNullableText = None
    last_name: CleanNullableText = None


class _TimeOfficePlanningUnitMembershipRow(TimeOfficeSourceRow):
    planning_unit_id: SourceInt
    employee_id: SourceInt
    membership_profession_id: SourceInt
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


class PersonnelRepositoryResult(SchedulingBaseModel):
    employees: tuple[Employee, ...]
    plan_participants: tuple[PlanParticipant, ...]
    planning_unit_memberships: tuple[PlanningUnitMembership, ...]


class TimeOfficePersonnelRepository:
    """Reads selected plan participants and active planning-unit memberships."""

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
        plans: tuple[Plan, ...],
        planning_unit_ids: tuple[int, ...],
        period: PlanningPeriod,
    ) -> PersonnelRepositoryResult:
        if not plans:
            return PersonnelRepositoryResult(
                employees=(),
                plan_participants=(),
                planning_unit_memberships=(),
            )

        plan_personnel_rows = self._fetch_plan_personnel_rows(
            connection=connection,
            plans=plans,
        )

        employees = self._deduplicate_employees(tuple(self._map_employee(row) for row in plan_personnel_rows))

        plan_participants = self._map_plan_participants(plan_personnel_rows)

        membership_rows = self._fetch_membership_rows(
            connection=connection,
            planning_unit_ids=planning_unit_ids,
            employee_ids=tuple(employee.employee_id for employee in employees),
            period=period,
        )

        return PersonnelRepositoryResult(
            employees=employees,
            plan_participants=plan_participants,
            planning_unit_memberships=self._map_memberships(membership_rows),
        )

    def _fetch_plan_personnel_rows(
        self,
        *,
        connection: Connection,
        plans: tuple[Plan, ...],
    ) -> tuple[_TimeOfficePlanPersonnelRow, ...]:
        query = text(
            """
            SELECT DISTINCT
                pp.RefPlan AS plan_id,
                p.RefPlanungseinheiten AS planning_unit_id,
                pp.RefPersonal AS employee_id,
                per.RefBerufe AS employee_profession_id,
                per.Vorname AS first_name,
                per.Name AS last_name
            FROM TPlanPersonal pp
            JOIN TPlan p
                ON p.Prim = pp.RefPlan
            JOIN TPersonal per
                ON per.Prim = pp.RefPersonal
            WHERE pp.RefPlan IN :plan_ids
            ORDER BY
                p.RefPlanungseinheiten,
                per.Name,
                per.Vorname,
                pp.RefPersonal
            """
        ).bindparams(bindparam("plan_ids", expanding=True))

        raw_rows = (
            connection.execute(
                query,
                {"plan_ids": tuple(plan.plan_id for plan in plans)},
            )
            .mappings()
            .all()
        )

        return tuple(_TimeOfficePlanPersonnelRow.model_validate(row) for row in raw_rows)

    def _fetch_membership_rows(
        self,
        *,
        connection: Connection,
        planning_unit_ids: tuple[int, ...],
        employee_ids: tuple[int, ...],
        period: PlanningPeriod,
    ) -> tuple[_TimeOfficePlanningUnitMembershipRow, ...]:
        if not planning_unit_ids or not employee_ids:
            return ()

        query = text(
            """
            SELECT DISTINCT
                pep.RefPlanungseinheiten AS planning_unit_id,
                pep.RefPersonal AS employee_id,
                pep.RefBerufe AS membership_profession_id,
                pep.VonDat AS valid_from,
                pep.BisDat AS valid_until,
                pep.IstHeimat AS is_home,
                pep.IstVonErsatz AS is_replacement
            FROM TPlanungseinheitenPersonal pep
            WHERE pep.RefPlanungseinheiten IN :planning_unit_ids
                AND pep.RefPersonal IN :employee_ids
                AND CONVERT(date, pep.VonDat) <= :period_end
                AND (
                    pep.BisDat IS NULL
                    OR CONVERT(date, pep.BisDat) >= :period_start
                )
                AND ISNULL(pep.KeinEPlan, 0) = 0
            ORDER BY
                planning_unit_id,
                employee_id,
                valid_from,
                valid_until
            """
        ).bindparams(
            bindparam("planning_unit_ids", expanding=True),
            bindparam("employee_ids", expanding=True),
        )

        raw_rows = (
            connection.execute(
                query,
                {
                    "planning_unit_ids": planning_unit_ids,
                    "employee_ids": employee_ids,
                    "period_start": period.start,
                    "period_end": period.end,
                },
            )
            .mappings()
            .all()
        )

        return tuple(_TimeOfficePlanningUnitMembershipRow.model_validate(row) for row in raw_rows)

    def _map_employee(self, row: _TimeOfficePlanPersonnelRow) -> Employee:
        return Employee(
            employee_id=row.employee_id,
            display_name=self._display_name(
                employee_id=row.employee_id,
                first_name=row.first_name,
                last_name=row.last_name,
            ),
            staff_level=self._staff_level_from_profession(
                row.employee_profession_id,
                context=f"TPersonal employee_id={row.employee_id}",
            ),
            capabilities=self._capabilities_for_employee(row.employee_id),
        )

    def _deduplicate_employees(self, employees: tuple[Employee, ...]) -> tuple[Employee, ...]:
        employees_by_id: dict[int, Employee] = {}

        for employee in employees:
            existing = employees_by_id.get(employee.employee_id)

            if existing is not None:
                if existing != employee:
                    raise ValueError(
                        "Conflicting duplicate employee rows from TPlanPersonal/TPersonal: "
                        f"employee_id={employee.employee_id} "
                        f"existing={existing!r} new={employee!r}."
                    )

                continue

            employees_by_id[employee.employee_id] = employee

        return tuple(
            sorted(
                employees_by_id.values(),
                key=lambda employee: employee.employee_id,
            )
        )

    def _map_plan_participants(self, rows: tuple[_TimeOfficePlanPersonnelRow, ...]) -> tuple[PlanParticipant, ...]:
        return tuple(
            PlanParticipant(
                plan_id=row.plan_id,
                planning_unit_id=row.planning_unit_id,
                employee_id=row.employee_id,
            )
            for row in rows
        )

    def _map_memberships(
        self, rows: tuple[_TimeOfficePlanningUnitMembershipRow, ...]
    ) -> tuple[PlanningUnitMembership, ...]:
        return tuple(
            PlanningUnitMembership(
                planning_unit_id=row.planning_unit_id,
                employee_id=row.employee_id,
                valid_from=row.valid_from.date(),
                valid_until=row.valid_until.date() if row.valid_until is not None else None,
                staff_level=self._staff_level_from_profession(
                    row.membership_profession_id,
                    context=(
                        "TPlanungseinheitenPersonal "
                        f"planning_unit_id={row.planning_unit_id} "
                        f"employee_id={row.employee_id}"
                    ),
                ),
                is_home=row.is_home,
                is_replacement=row.is_replacement,
            )
            for row in rows
        )

    def _staff_level_from_profession(self, profession_id: int, *, context: str) -> StaffLevel:
        staff_level = self._facts.staff_level_by_profession_id_map.get(profession_id)

        if staff_level is None:
            raise ValueError(
                f"No StaffLevel mapping configured for TimeOffice profession_id={profession_id} in {context}."
            )

        return staff_level

    def _capabilities_for_employee(self, employee_id: int) -> tuple[Capability, ...]:
        return tuple(self._facts.capabilities_by_employee_id_map.get(employee_id, ()))

    def _display_name(
        self,
        *,
        employee_id: int,
        first_name: str | None,
        last_name: str | None,
    ) -> str:
        display_name = " ".join(part for part in (last_name, first_name) if part)

        if display_name:
            return display_name

        return f"Employee {employee_id}"
