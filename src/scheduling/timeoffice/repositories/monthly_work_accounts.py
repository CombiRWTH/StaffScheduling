from sqlalchemy import Connection, bindparam, text

from scheduling.domain import Employee, MonthlyWorkAccount, PlanningMonth, SchedulingBaseModel
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.repositories.types import (
    SourceInt,
    TimeOfficeSourceRow,
)


class _TimeOfficeMonthlyWorkAccountRow(TimeOfficeSourceRow):
    employee_id: SourceInt
    month: SourceInt
    target_hours: float | None = None
    actual_hours: float | None = None


class TimeOfficeMonthlyWorkAccountRepositoryResult(SchedulingBaseModel):
    monthly_work_accounts: tuple[MonthlyWorkAccount, ...]


class TimeOfficeMonthlyWorkAccountRepository:
    """Reads monthly target and actual work hours from TimeOffice account values."""

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
        employees: tuple[Employee, ...],
        planning_month: PlanningMonth,
    ) -> TimeOfficeMonthlyWorkAccountRepositoryResult:
        if not employees:
            return TimeOfficeMonthlyWorkAccountRepositoryResult(monthly_work_accounts=())

        rows = self._fetch_rows(
            connection=connection,
            employee_ids=tuple(employee.employee_id for employee in employees),
            month=self._timeoffice_month(planning_month),
        )

        self._validate_unique_employee_rows(rows)

        return TimeOfficeMonthlyWorkAccountRepositoryResult(monthly_work_accounts=self._map_accounts(rows))

    def _fetch_rows(
        self,
        *,
        connection: Connection,
        employee_ids: tuple[int, ...],
        month: int,
    ) -> tuple[_TimeOfficeMonthlyWorkAccountRow, ...]:
        query = text(
            """
            SELECT
                target.RefPersonal AS employee_id,
                target.Monat AS month,
                target.Wert2 AS target_hours,
                actual.Wert2 AS actual_hours
            FROM TPersonalKontenJeMonat target
            LEFT JOIN TPersonalKontenJeMonat actual
                ON actual.RefPersonal = target.RefPersonal
                AND actual.Monat = target.Monat
                AND actual.RefKonten = :actual_account_id
            WHERE target.RefPersonal IN :employee_ids
                AND target.Monat = :month
                AND target.RefKonten = :target_account_id
            ORDER BY
                target.RefPersonal
            """
        ).bindparams(bindparam("employee_ids", expanding=True))

        raw_rows = (
            connection.execute(
                query,
                {
                    "employee_ids": employee_ids,
                    "month": month,
                    "target_account_id": self._facts.monthly_target_work_account_id,
                    "actual_account_id": self._facts.monthly_actual_work_account_id,
                },
            )
            .mappings()
            .all()
        )

        return tuple(_TimeOfficeMonthlyWorkAccountRow.model_validate(row) for row in raw_rows)

    def _validate_unique_employee_rows(
        self,
        rows: tuple[_TimeOfficeMonthlyWorkAccountRow, ...],
    ) -> None:
        seen_employee_ids: set[int] = set()

        for row in rows:
            if row.employee_id in seen_employee_ids:
                raise ValueError(
                    "Duplicate TimeOffice monthly work target account row for "
                    f"employee_id={row.employee_id} month={row.month}."
                )

            seen_employee_ids.add(row.employee_id)

    def _map_accounts(
        self,
        rows: tuple[_TimeOfficeMonthlyWorkAccountRow, ...],
    ) -> tuple[MonthlyWorkAccount, ...]:
        accounts: list[MonthlyWorkAccount] = []

        for row in rows:
            target_minutes = self._hours_to_minutes(row.target_hours)

            if target_minutes <= 0:
                continue

            actual_minutes = self._hours_to_minutes(row.actual_hours)

            accounts.append(
                MonthlyWorkAccount(
                    employee_id=row.employee_id,
                    target_minutes=target_minutes,
                    actual_minutes=actual_minutes if actual_minutes > 0 else None,
                )
            )

        return tuple(sorted(accounts, key=lambda account: account.employee_id))

    def _timeoffice_month(self, planning_month: PlanningMonth) -> int:
        return planning_month.year * 100 + planning_month.month

    def _hours_to_minutes(self, value: float | None) -> int:
        if value is None:
            return 0

        return round(value * 60)
