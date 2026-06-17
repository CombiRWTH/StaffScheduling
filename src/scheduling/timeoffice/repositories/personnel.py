from sqlalchemy import Connection, bindparam, text
from sqlalchemy.engine import RowMapping

from src.scheduling.models import (
    Capability,
    Employee,
    Plan,
    PlanningPeriod,
    PlanningUnitMembership,
    PlanParticipant,
    SchedulingBaseModel,
    StaffLevel,
)
from src.scheduling.timeoffice.facts import TimeOfficeFacts
from src.scheduling.timeoffice.repositories.helpers import clean_text, required, to_datetime


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

        employees = self._map_employees(plan_personnel_rows)
        plan_participants = tuple(self._map_plan_participant(row) for row in plan_personnel_rows)

        employee_ids = tuple(employee.employee_id for employee in employees)

        memberships = self._fetch_memberships(
            connection=connection,
            planning_unit_ids=planning_unit_ids,
            employee_ids=employee_ids,
            period=period,
        )

        return PersonnelRepositoryResult(
            employees=employees,
            plan_participants=plan_participants,
            planning_unit_memberships=memberships,
        )

    def _fetch_plan_personnel_rows(
        self,
        *,
        connection: Connection,
        plans: tuple[Plan, ...],
    ) -> tuple[RowMapping, ...]:
        plan_ids = tuple(plan.plan_id for plan in plans)

        return tuple(
            connection.execute(
                self._plan_personnel_query(),
                {"plan_ids": plan_ids},
            )
            .mappings()
            .all()
        )

    def _fetch_memberships(
        self,
        *,
        connection: Connection,
        planning_unit_ids: tuple[int, ...],
        employee_ids: tuple[int, ...],
        period: PlanningPeriod,
    ) -> tuple[PlanningUnitMembership, ...]:
        if not planning_unit_ids or not employee_ids:
            return ()

        rows = tuple(
            connection.execute(
                self._membership_query(),
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

        return tuple(self._map_membership(row) for row in rows)

    def _plan_personnel_query(self):
        return text(
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

    def _membership_query(self):
        return text(
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

    def _map_employees(self, rows: tuple[RowMapping, ...]) -> tuple[Employee, ...]:
        employees_by_id: dict[int, Employee] = {}

        for row in rows:
            employee_id = int(
                required(
                    row["employee_id"],
                    field_name="employee_id",
                    context="TPlanPersonal",
                )
            )

            employee_profession_id = int(
                required(
                    row["employee_profession_id"],
                    field_name="employee_profession_id",
                    context=f"TPersonal employee_id={employee_id}",
                )
            )

            employee = Employee(
                employee_id=employee_id,
                display_name=self._display_name(
                    employee_id=employee_id,
                    first_name=row["first_name"],
                    last_name=row["last_name"],
                ),
                staff_level=self._staff_level_from_profession(
                    employee_profession_id,
                    context=f"TPersonal employee_id={employee_id}",
                ),
                capabilities=self._capabilities_for_employee(employee_id),
            )

            existing = employees_by_id.get(employee_id)
            if existing is not None:
                if (
                    existing.display_name != employee.display_name
                    or existing.staff_level != employee.staff_level
                    or existing.capabilities != employee.capabilities
                ):
                    raise ValueError(
                        "Conflicting duplicate employee rows from TPlanPersonal/TPersonal: "
                        f"employee_id={employee_id} "
                        f"existing={existing!r} new={employee!r}."
                    )

                continue

            employees_by_id[employee_id] = employee

        return tuple(
            sorted(
                employees_by_id.values(),
                key=lambda employee: employee.employee_id,
            )
        )

    def _map_plan_participant(self, row: RowMapping) -> PlanParticipant:
        return PlanParticipant(
            plan_id=int(
                required(
                    row["plan_id"],
                    field_name="plan_id",
                    context="TPlanPersonal",
                )
            ),
            planning_unit_id=int(
                required(
                    row["planning_unit_id"],
                    field_name="planning_unit_id",
                    context="TPlanPersonal",
                )
            ),
            employee_id=int(
                required(
                    row["employee_id"],
                    field_name="employee_id",
                    context="TPlanPersonal",
                )
            ),
        )

    def _map_membership(self, row: RowMapping) -> PlanningUnitMembership:
        planning_unit_id = int(
            required(
                row["planning_unit_id"],
                field_name="planning_unit_id",
                context="TPlanungseinheitenPersonal",
            )
        )
        employee_id = int(
            required(
                row["employee_id"],
                field_name="employee_id",
                context="TPlanungseinheitenPersonal",
            )
        )

        membership_profession_id = int(
            required(
                row["membership_profession_id"],
                field_name="membership_profession_id",
                context=(f"TPlanungseinheitenPersonal planning_unit_id={planning_unit_id} employee_id={employee_id}"),
            )
        )

        valid_from = required(
            to_datetime(row["valid_from"]),
            field_name="valid_from",
            context=(f"TPlanungseinheitenPersonal planning_unit_id={planning_unit_id} employee_id={employee_id}"),
        ).date()

        valid_until = to_datetime(row["valid_until"]).date() if row["valid_until"] is not None else None

        return PlanningUnitMembership(
            planning_unit_id=planning_unit_id,
            employee_id=employee_id,
            valid_from=valid_from,
            valid_until=valid_until,
            staff_level=self._staff_level_from_profession(
                membership_profession_id,
                context=(f"TPlanungseinheitenPersonal planning_unit_id={planning_unit_id} employee_id={employee_id}"),
            ),
            is_home=bool(
                required(
                    row["is_home"],
                    field_name="is_home",
                    context="TPlanungseinheitenPersonal",
                )
            ),
            is_replacement=bool(
                required(
                    row["is_replacement"],
                    field_name="is_replacement",
                    context="TPlanungseinheitenPersonal",
                )
            ),
        )

    def _staff_level_from_profession(
        self,
        profession_id: int,
        *,
        context: str,
    ) -> StaffLevel:
        staff_level = self._facts.profession_staff_level_map.get(profession_id)
        if staff_level is None:
            raise ValueError(
                f"No StaffLevel mapping configured for TimeOffice profession_id={profession_id} in {context}."
            )

        return staff_level

    def _capabilities_for_employee(self, employee_id: int) -> tuple[Capability, ...]:
        return tuple(self._facts.employee_capabilities_map.get(employee_id, ()))

    def _display_name(
        self,
        *,
        employee_id: int,
        first_name: object,
        last_name: object,
    ) -> str:
        first = clean_text(first_name)
        last = clean_text(last_name)

        display_name = " ".join(part for part in (last, first) if part)
        if display_name:
            return display_name

        return f"Employee {employee_id}"
