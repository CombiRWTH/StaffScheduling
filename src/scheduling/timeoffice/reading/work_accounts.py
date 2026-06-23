from sqlalchemy import Connection, bindparam, text

from scheduling.domain import PlanningMonth
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.reading.types import SourceInt, TimeOfficeSourceRow


class TimeOfficeMonthlyWorkAccountRow(TimeOfficeSourceRow):
    employee_id: SourceInt
    month: SourceInt
    target_hours: float | None = None
    actual_hours: float | None = None


class TimeOfficeMonthlyWorkAccountReader:
    """Reads monthly target and actual work-account source rows."""

    def __init__(self, *, facts: TimeOfficeFacts) -> None:
        self._facts = facts

    def read_rows(
        self,
        *,
        connection: Connection,
        employee_ids: tuple[int, ...],
        planning_month: PlanningMonth,
    ) -> tuple[TimeOfficeMonthlyWorkAccountRow, ...]:
        if not employee_ids:
            return ()

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
                    "month": _timeoffice_month(planning_month),
                    "target_account_id": self._facts.monthly_target_work_account_id,
                    "actual_account_id": self._facts.monthly_actual_work_account_id,
                },
            )
            .mappings()
            .all()
        )

        return tuple(TimeOfficeMonthlyWorkAccountRow.model_validate(row) for row in raw_rows)


def _timeoffice_month(planning_month: PlanningMonth) -> int:
    return planning_month.year * 100 + planning_month.month
