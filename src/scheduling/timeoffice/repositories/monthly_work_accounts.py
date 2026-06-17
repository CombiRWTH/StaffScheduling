from typing import Self

from pydantic import model_validator
from sqlalchemy import Connection, bindparam, text

from scheduling.models import Employee, MonthlyWorkAccount, PlanningPeriod, SchedulingBaseModel
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.repositories.types import (
    CleanNullableText,
    SourceInt,
    SourceNullableInt,
    TimeOfficeSourceRow,
)


class _TimeOfficeMonthlyWorkAccountRow(TimeOfficeSourceRow):
    employee_id: SourceInt
    month: SourceInt

    target_account_id: SourceInt
    target_account_code: CleanNullableText = None
    target_account_name: CleanNullableText = None
    target_account_short_name: CleanNullableText = None
    target_hours: float | None = None

    actual_account_id: SourceNullableInt = None
    actual_account_code: CleanNullableText = None
    actual_account_name: CleanNullableText = None
    actual_account_short_name: CleanNullableText = None
    actual_hours: float | None = None

    @model_validator(mode="after")
    def validate_actual_account_shape(self) -> Self:
        if self.actual_account_id is None and self.actual_hours is not None:
            raise ValueError(
                "Monthly actual hours are present without an actual account id: "
                f"employee_id={self.employee_id} "
                f"month={self.month} "
                f"actual_hours={self.actual_hours!r}."
            )

        return self


class TimeOfficeMonthlyWorkAccountRepositoryResult(SchedulingBaseModel):
    monthly_work_accounts: tuple[MonthlyWorkAccount, ...]


class TimeOfficeMonthlyWorkAccountRepository:
    """Reads monthly target/actual work account values from TimeOffice.

    Source:
    - TPersonalKontenJeMonat.Monat is YYYYMM
    - RefKonten=1 / SOLL_MONAT provides target monthly hours in Wert2
    - RefKonten=55 / TOTAL provides actual monthly hours in Wert2

    Rows with target_minutes <= 0 are intentionally not emitted because an
    all-zero target would be misleading for scheduling.
    """

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def fetch(
        self,
        *,
        connection: Connection,
        employees: tuple[Employee, ...],
        period: PlanningPeriod,
    ) -> TimeOfficeMonthlyWorkAccountRepositoryResult:
        if not employees:
            return TimeOfficeMonthlyWorkAccountRepositoryResult(monthly_work_accounts=())

        rows = self._fetch_rows(
            connection=connection,
            employees=employees,
            month=self._month(period),
        )

        self._validate_unique_employee_rows(rows)

        return TimeOfficeMonthlyWorkAccountRepositoryResult(monthly_work_accounts=self._map_accounts(rows))

    def _fetch_rows(
        self,
        *,
        connection: Connection,
        employees: tuple[Employee, ...],
        month: int,
    ) -> tuple[_TimeOfficeMonthlyWorkAccountRow, ...]:
        query = text(
            """
            SELECT
                target.RefPersonal AS employee_id,
                target.Monat AS month,

                target.RefKonten AS target_account_id,
                target_account.BezProg AS target_account_code,
                target_account.Bez AS target_account_name,
                target_account.BezKurz AS target_account_short_name,
                target.Wert2 AS target_hours,

                actual.RefKonten AS actual_account_id,
                actual_account.BezProg AS actual_account_code,
                actual_account.Bez AS actual_account_name,
                actual_account.BezKurz AS actual_account_short_name,
                actual.Wert2 AS actual_hours
            FROM TPersonalKontenJeMonat target
            JOIN TKonten target_account
                ON target_account.Prim = target.RefKonten
            LEFT JOIN TPersonalKontenJeMonat actual
                ON actual.RefPersonal = target.RefPersonal
                AND actual.Monat = target.Monat
                AND actual.RefKonten = :actual_account_id
            LEFT JOIN TKonten actual_account
                ON actual_account.Prim = actual.RefKonten
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
                    "employee_ids": tuple(employee.employee_id for employee in employees),
                    "month": month,
                    "target_account_id": self._facts.monthly_target_work_account_id,
                    "actual_account_id": self._facts.monthly_actual_work_account_id,
                },
            )
            .mappings()
            .all()
        )

        return tuple(_TimeOfficeMonthlyWorkAccountRow.model_validate(row) for row in raw_rows)

    def _validate_unique_employee_rows(self, rows: tuple[_TimeOfficeMonthlyWorkAccountRow, ...]) -> None:
        seen_employee_ids: set[int] = set()

        for row in rows:
            if row.employee_id in seen_employee_ids:
                raise ValueError(
                    "Duplicate TimeOffice monthly work target account row for "
                    f"employee_id={row.employee_id} month={row.month!r}."
                )

            seen_employee_ids.add(row.employee_id)

    def _map_accounts(self, rows: tuple[_TimeOfficeMonthlyWorkAccountRow, ...]) -> tuple[MonthlyWorkAccount, ...]:
        accounts: list[MonthlyWorkAccount] = []

        for row in rows:
            target_minutes = self._hours_to_minutes(row.target_hours)

            if target_minutes <= 0:
                continue

            accounts.append(
                MonthlyWorkAccount(
                    employee_id=row.employee_id,
                    target_minutes=target_minutes,
                    actual_minutes=self._optional_hours_to_minutes(row.actual_hours),
                )
            )

        return tuple(sorted(accounts, key=lambda account: account.employee_id))

    def _month(self, period: PlanningPeriod) -> int:
        if period.start.year != period.end.year or period.start.month != period.end.month:
            raise ValueError(
                "Monthly work accounts can only be imported for a single calendar month. "
                f"Got period {period.start}..{period.end}."
            )

        return period.start.year * 100 + period.start.month

    def _hours_to_minutes(self, value: float | None) -> int:
        if value is None:
            return 0

        return round(value * 60)

    def _optional_hours_to_minutes(self, value: float | None) -> int | None:
        minutes = self._hours_to_minutes(value)
        return minutes if minutes > 0 else None
