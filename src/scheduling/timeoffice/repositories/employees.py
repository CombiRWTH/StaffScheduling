from datetime import date as Date

from pydantic import BaseModel, Field
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Connection

from src.scheduling.models.employee import Employee
from src.scheduling.models.relations import Membership, MembershipType
from src.scheduling.timeoffice.repositories.helpers import to_date
from src.scheduling.timeoffice.repositories.plans import TimeOfficePlan


class TimeOfficePlanEmployee(BaseModel):
    """Employee assigned to a concrete TimeOffice monthly plan."""

    source_plan_employee_id: int = Field(gt=0)
    source_plan_id: int = Field(gt=0)

    station_id: int = Field(gt=0)
    employee_id: int = Field(gt=0)

    personnel_number: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    short_name: str | None = None

    source_profession_id: int | None = None

    valid_from: Date | None = None
    valid_until: Date | None = None

    is_substitute: bool | None = None


class EmployeeRepositoryResult(BaseModel):
    """Canonical output of reading TimeOffice plan employees."""

    employees: tuple[Employee, ...]
    memberships: tuple[Membership, ...]


class TimeOfficeEmployeeRepository:
    """Read TimeOffice plan employees and map them to employees/memberships."""

    def fetch(
        self,
        connection: Connection,
        plans: tuple[TimeOfficePlan, ...],
    ) -> EmployeeRepositoryResult:
        """Read employees assigned to selected monthly TimeOffice plans."""
        source_plan_ids = tuple(plan.source_plan_id for plan in plans)

        if not source_plan_ids:
            raise ValueError("Cannot read TimeOffice employees without source plan ids.")

        query = text(
            """
            SELECT
                pp.Prim AS source_plan_employee_id,
                pp.RefPlan AS source_plan_id,
                tp.RefPlanungseinheiten AS station_id,
                pp.RefPersonal AS employee_id,

                p.PersNr AS personnel_number,
                p.Vorname AS first_name,
                p.Name AS last_name,
                p.KurzName AS short_name,

                pp.RefBerufe AS source_profession_id,
                pp.VonDat AS valid_from,
                pp.BisDat AS valid_until,
                pp.IstVonErsatz AS is_substitute
            FROM TPlanPersonal pp
            JOIN TPlan tp
                ON tp.Prim = pp.RefPlan
            JOIN TPersonal p
                ON p.Prim = pp.RefPersonal
            WHERE pp.RefPlan IN :source_plan_ids
            """
        ).bindparams(bindparam("source_plan_ids", expanding=True))

        rows = (
            connection.execute(
                query,
                {
                    "source_plan_ids": source_plan_ids,
                },
            )
            .mappings()
            .all()
        )

        source_employees = tuple(
            TimeOfficePlanEmployee(
                source_plan_employee_id=row["source_plan_employee_id"],
                source_plan_id=row["source_plan_id"],
                station_id=row["station_id"],
                employee_id=row["employee_id"],
                personnel_number=row["personnel_number"],
                first_name=row["first_name"],
                last_name=row["last_name"],
                short_name=row["short_name"],
                source_profession_id=row["source_profession_id"],
                valid_from=to_date(row["valid_from"]),
                valid_until=to_date(row["valid_until"]),
                is_substitute=None if row["is_substitute"] is None else bool(row["is_substitute"]),
            )
            for row in rows
        )

        self._ensure_rows_reference_known_plans(source_plan_ids, source_employees)

        employees_by_id: dict[int, Employee] = {}
        memberships_by_key: dict[tuple[int, int], Membership] = {}

        for source_employee in source_employees:
            employees_by_id[source_employee.employee_id] = self._map_employee(source_employee)

            membership = self._map_membership(source_employee)
            memberships_by_key[(membership.employee_id, membership.station_id)] = membership

        print(f"[timeoffice] database.repository.employees rows={len(source_employees)}")

        return EmployeeRepositoryResult(
            employees=tuple(employees_by_id.values()),
            memberships=tuple(memberships_by_key.values()),
        )

    def _map_employee(self, source_employee: TimeOfficePlanEmployee) -> Employee:
        """Map a TimeOffice plan employee row to a canonical Employee."""
        return Employee(
            employee_id=source_employee.employee_id,
            personnel_number=source_employee.personnel_number,
            first_name=source_employee.first_name,
            last_name=source_employee.last_name,
            display_name=self._display_name(source_employee),
            group_id=None,
            active=True,
        )

    def _map_membership(self, source_employee: TimeOfficePlanEmployee) -> Membership:
        """Map a TimeOffice plan employee row to a local station membership."""
        return Membership(
            employee_id=source_employee.employee_id,
            station_id=source_employee.station_id,
            membership_type=MembershipType.LOCAL,
            valid_from=source_employee.valid_from,
            valid_until=source_employee.valid_until,
            is_substitute=source_employee.is_substitute,
        )

    def _display_name(self, source_employee: TimeOfficePlanEmployee) -> str:
        """Build a readable employee display name."""
        display_name = " ".join(
            part
            for part in (
                source_employee.first_name,
                source_employee.last_name,
            )
            if part
        )

        if display_name:
            return display_name

        if source_employee.short_name:
            return source_employee.short_name

        if source_employee.personnel_number:
            return source_employee.personnel_number

        return f"Employee {source_employee.employee_id}"

    def _ensure_rows_reference_known_plans(
        self,
        known_source_plan_ids: tuple[int, ...],
        source_employees: tuple[TimeOfficePlanEmployee, ...],
    ) -> None:
        """Ensure employee rows only reference selected plans."""
        known_source_plan_id_set = set(known_source_plan_ids)

        unknown_source_plan_ids = sorted(
            {
                source_employee.source_plan_id
                for source_employee in source_employees
                if source_employee.source_plan_id not in known_source_plan_id_set
            }
        )

        if unknown_source_plan_ids:
            raise ValueError(f"Employee rows reference unknown TimeOffice plan ids: {unknown_source_plan_ids}")
