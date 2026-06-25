from scheduling.domain import EmployeeSundayWorkHistory
from scheduling.timeoffice.reading.sunday_work import TimeOfficeSundayHistoryRow


def map_sunday_work_history(
    rows: tuple[TimeOfficeSundayHistoryRow, ...],
) -> tuple[EmployeeSundayWorkHistory, ...]:
    return tuple(
        EmployeeSundayWorkHistory(
            employee_id=row.employee_id,
            worked_sundays=row.worked_sundays,
        )
        for row in rows
    )
