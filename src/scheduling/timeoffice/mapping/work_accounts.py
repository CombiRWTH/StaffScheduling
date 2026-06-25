from scheduling.domain import MonthlyWorkAccount
from scheduling.timeoffice.reading.work_accounts import TimeOfficeMonthlyWorkAccountRow


def map_monthly_work_accounts(
    rows: tuple[TimeOfficeMonthlyWorkAccountRow, ...],
) -> tuple[MonthlyWorkAccount, ...]:
    accounts: list[MonthlyWorkAccount] = []

    for row in rows:
        target_minutes = _hours_to_minutes(row.target_hours)
        if target_minutes <= 0:
            continue

        actual_minutes = _hours_to_minutes(row.actual_hours)

        accounts.append(
            MonthlyWorkAccount(
                employee_id=row.employee_id,
                target_minutes=target_minutes,
                actual_minutes=actual_minutes if actual_minutes > 0 else None,
            )
        )

    return tuple(sorted(accounts, key=lambda account: account.employee_id))


def _hours_to_minutes(value: float | None) -> int:
    if value is None:
        return 0

    return round(value * 60)
