from math import isfinite

from app.domain import MonthlyWorkAccount
from app.timeoffice.reading.work_accounts import TimeOfficeMonthlyWorkAccountRow


def map_monthly_work_accounts(
    rows: tuple[TimeOfficeMonthlyWorkAccountRow, ...],
) -> tuple[MonthlyWorkAccount, ...]:
    accounts: list[MonthlyWorkAccount] = []

    for row in rows:
        target_minutes = _hours_to_minutes(row.target_hours)
        actual_minutes = _hours_to_minutes(row.actual_hours) if row.actual_hours is not None else None

        accounts.append(
            MonthlyWorkAccount(
                employee_id=row.employee_id,
                target_minutes=target_minutes,
                actual_minutes=actual_minutes if row.actual_hours is not None else None,
            )
        )

    return tuple(sorted(accounts, key=lambda account: account.employee_id))


def _hours_to_minutes(value: float | None) -> int:
    if value is None:
        raise ValueError("Missing monthly work-account hours.")

    if not isfinite(value) or value < 0:
        raise ValueError("Monthly work-account hours must be finite and nonnegative.")
    return round(value * 60)
