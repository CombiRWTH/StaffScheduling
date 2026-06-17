from datetime import date as Date

from sqlalchemy import Connection, bindparam, text
from sqlalchemy.engine import RowMapping

from src.scheduling.models import (
    Employee,
    EmployeeSundayWorkHistory,
    PlanningPeriod,
    SchedulingBaseModel,
)


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

        employee_ids = tuple(employee.employee_id for employee in employees)
        sunday_account_id = self._fetch_sunday_account_id(connection)

        lookback_start = self._subtract_years(period.end, self.LOOKBACK_YEARS)
        lookback_end = period.end

        rows = connection.execute(
            self._history_query(),
            {
                "employee_ids": employee_ids,
                "sunday_account_id": sunday_account_id,
                "lookback_start": lookback_start,
                "lookback_end": lookback_end,
            },
        ).mappings()

        return SundayWorkHistoryRepositoryResult(sunday_work_history=tuple(self._map_history_row(row) for row in rows))

    def _fetch_sunday_account_id(self, connection: Connection) -> int:
        rows = (
            connection.execute(
                self._sunday_account_query(),
                {"sunday_account_code": self.SUNDAY_ACCOUNT_CODE},
            )
            .mappings()
            .all()
        )

        if len(rows) != 1:
            raise ValueError(
                "Expected exactly one TimeOffice Sunday account with "
                f"BezProg={self.SUNDAY_ACCOUNT_CODE!r}, found {len(rows)}."
            )

        row = rows[0]
        is_daily_account = int(row["is_daily_account"] or 0)

        if is_daily_account != 1:
            raise ValueError(
                "TimeOffice Sunday account must be a daily account: "
                f"account_id={row['account_id']} "
                f"code={row['account_code']!r} "
                f"name={row['account_name']!r}."
            )

        return int(row["account_id"])

    def _sunday_account_query(self):
        return text("""
            SELECT
                Prim AS account_id,
                BezProg AS account_code,
                Bez AS account_name,
                BezKurz AS account_short_name,
                IstTagesKonto AS is_daily_account
            FROM TKonten
            WHERE BezProg = :sunday_account_code
        """)

    def _history_query(self):
        return text("""
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

    def _map_history_row(self, row: RowMapping) -> EmployeeSundayWorkHistory:
        return EmployeeSundayWorkHistory(
            employee_id=int(row["employee_id"]),
            worked_sundays=int(row["worked_sundays"] or 0),
        )

    def _subtract_years(self, value: Date, years: int) -> Date:
        try:
            return value.replace(year=value.year - years)
        except ValueError:
            # Leap day fallback.
            return value.replace(year=value.year - years, day=28)
