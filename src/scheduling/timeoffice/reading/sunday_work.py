from datetime import date

from sqlalchemy import Connection, bindparam, text

from scheduling.domain import PlanningMonth
from scheduling.timeoffice.reading.types import CleanNullableText, SourceInt, TimeOfficeSourceRow


class TimeOfficeSundayAccountRow(TimeOfficeSourceRow):
    account_id: SourceInt
    account_code: CleanNullableText = None
    account_name: CleanNullableText = None
    is_daily_account: bool | None = None


class TimeOfficeSundayHistoryRow(TimeOfficeSourceRow):
    employee_id: SourceInt
    worked_sundays: SourceInt


class TimeOfficeSundayWorkHistoryReader:
    """Reads historical worked-Sunday count source rows from TimeOffice."""

    LOOKBACK_YEARS = 1
    SUNDAY_ACCOUNT_CODE = "SONNTAG"

    def read_rows(
        self,
        *,
        connection: Connection,
        employee_ids: tuple[int, ...],
        planning_month: PlanningMonth,
    ) -> tuple[TimeOfficeSundayHistoryRow, ...]:
        if not employee_ids:
            return ()

        sunday_account_id = self._read_sunday_account_id(connection)

        query = text(
            """
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
            """
        ).bindparams(bindparam("employee_ids", expanding=True))

        raw_rows = (
            connection.execute(
                query,
                {
                    "employee_ids": employee_ids,
                    "sunday_account_id": sunday_account_id,
                    "lookback_start": _subtract_years(planning_month.end, self.LOOKBACK_YEARS),
                    "lookback_end": planning_month.end,
                },
            )
            .mappings()
            .all()
        )

        return tuple(TimeOfficeSundayHistoryRow.model_validate(row) for row in raw_rows)

    def _read_sunday_account_id(self, connection: Connection) -> int:
        query = text(
            """
            SELECT
                Prim AS account_id,
                BezProg AS account_code,
                Bez AS account_name,
                IstTagesKonto AS is_daily_account
            FROM TKonten
            WHERE BezProg = :sunday_account_code
            """
        )

        rows = tuple(
            TimeOfficeSundayAccountRow.model_validate(row)
            for row in connection.execute(
                query,
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

        if row.is_daily_account is not True:
            raise ValueError(
                "TimeOffice Sunday account must be a daily account: "
                f"account_id={row.account_id} "
                f"code={row.account_code!r} "
                f"name={row.account_name!r}."
            )

        return row.account_id


def _subtract_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year - years)
    except ValueError:
        return value.replace(year=value.year - years, day=28)
