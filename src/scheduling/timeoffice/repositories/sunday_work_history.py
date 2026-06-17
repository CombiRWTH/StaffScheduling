from datetime import date

from sqlalchemy import Connection, bindparam, text

from scheduling.models import Employee, EmployeeSundayWorkHistory, PlanningPeriod, SchedulingBaseModel
from scheduling.timeoffice.repositories.types import CleanNullableText, SourceInt, TimeOfficeSourceRow


class _TimeOfficeSundayAccountRow(TimeOfficeSourceRow):
    account_id: SourceInt
    account_code: CleanNullableText = None
    account_name: CleanNullableText = None
    is_daily_account: bool | None = None


class _TimeOfficeSundayHistoryRow(TimeOfficeSourceRow):
    employee_id: SourceInt
    worked_sundays: SourceInt


class SundayWorkHistoryRepositoryResult(SchedulingBaseModel):
    sunday_work_history: tuple[EmployeeSundayWorkHistory, ...]


class TimeOfficeSundayWorkHistoryRepository:
    """Reads historical worked-Sunday counts from TimeOffice daily account rows.

    Source:
        - TKonten identifies the Sunday account via BezProg = 'SONNTAG'
        - TPersonalKontenJeTag contains daily account rows

    This repository intentionally does not use TimeOfficeFacts because the
    account identity is inferable from the database.
    """

    LOOKBACK_YEARS = 1
    SUNDAY_ACCOUNT_CODE = "SONNTAG"

    def fetch(
        self,
        *,
        connection: Connection,
        period: PlanningPeriod,
        employees: tuple[Employee, ...],
    ) -> SundayWorkHistoryRepositoryResult:
        if not employees:
            return SundayWorkHistoryRepositoryResult(sunday_work_history=())

        sunday_account_id = self._fetch_sunday_account_id(connection)

        rows = self._fetch_history_rows(
            connection=connection,
            employees=employees,
            sunday_account_id=sunday_account_id,
            lookback_start=self._subtract_years(period.end, self.LOOKBACK_YEARS),
            lookback_end=period.end,
        )

        return SundayWorkHistoryRepositoryResult(sunday_work_history=self._map_history_rows(rows))

    def _fetch_sunday_account_id(self, connection: Connection) -> int:
        query = text("""
            SELECT
                Prim AS account_id,
                BezProg AS account_code,
                Bez AS account_name,
                IstTagesKonto AS is_daily_account
            FROM TKonten
            WHERE BezProg = :sunday_account_code
        """)

        rows = tuple(
            _TimeOfficeSundayAccountRow.model_validate(row)
            for row in connection.execute(query, {"sunday_account_code": self.SUNDAY_ACCOUNT_CODE}).mappings().all()
        )

        if len(rows) != 1:
            raise ValueError(
                "Expected exactly one TimeOffice Sunday account with "
                f"BezProg={self.SUNDAY_ACCOUNT_CODE!r}, found {len(rows)}."
            )

        row = rows[0]

        if row.is_daily_account is not True:
            raise ValueError(
                "TimeOffice Sunday account must be a daily account: "
                f"account_id={row.account_id} "
                f"code={row.account_code!r} "
                f"name={row.account_name!r}."
            )

        return row.account_id

    def _fetch_history_rows(
        self,
        *,
        connection: Connection,
        employees: tuple[Employee, ...],
        sunday_account_id: int,
        lookback_start: date,
        lookback_end: date,
    ) -> tuple[_TimeOfficeSundayHistoryRow, ...]:
        query = text("""
            SELECT
                p.Prim AS employee_id,
                COUNT(DISTINCT CAST(pkt.Datum AS date)) AS worked_sundays
            FROM TPersonal p
            LEFT JOIN TPersonalKontenJeTag pkt
                ON pkt.RefPersonal = p.Prim
                AND pkt.RefKonten = :sunday_account_id
                AND CAST(pkt.Datum AS date) BETWEEN :lookback_start AND :lookback_end
                AND DATEDIFF(
                    day,
                    CONVERT(date, '1900-01-07', 23),
                    CAST(pkt.Datum AS date)
                ) % 7 = 0
                AND ISNULL(pkt.Wert, 0) > 0
            WHERE p.Prim IN :employee_ids
            GROUP BY p.Prim
            ORDER BY p.Prim
        """).bindparams(bindparam("employee_ids", expanding=True))

        raw_rows = (
            connection.execute(
                query,
                {
                    "employee_ids": tuple(employee.employee_id for employee in employees),
                    "sunday_account_id": sunday_account_id,
                    "lookback_start": lookback_start,
                    "lookback_end": lookback_end,
                },
            )
            .mappings()
            .all()
        )

        return tuple(_TimeOfficeSundayHistoryRow.model_validate(row) for row in raw_rows)

    def _map_history_rows(self, rows: tuple[_TimeOfficeSundayHistoryRow, ...]) -> tuple[EmployeeSundayWorkHistory, ...]:
        return tuple(self._map_history_row(row) for row in rows)

    def _map_history_row(self, row: _TimeOfficeSundayHistoryRow) -> EmployeeSundayWorkHistory:
        return EmployeeSundayWorkHistory(
            employee_id=row.employee_id,
            worked_sundays=row.worked_sundays,
        )

    def _subtract_years(self, value: date, years: int) -> date:
        try:
            return value.replace(year=value.year - years)
        except ValueError:
            # Leap day fallback.
            return value.replace(year=value.year - years, day=28)
