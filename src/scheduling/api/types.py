from datetime import date as Date
from datetime import datetime as DateTime
from typing import Annotated, Any

from pydantic import BeforeValidator


def parse_api_date(value: Any) -> Date:
    """Parse API date values.

    Primary API format is ISO: YYYY-MM-DD.
    DD.MM.YYYY is accepted for compatibility with previous CLI usage.
    """
    if isinstance(value, Date) and not isinstance(value, DateTime):
        return value

    if isinstance(value, DateTime):
        return value.date()

    if not isinstance(value, str):
        raise ValueError("Date must be a string in YYYY-MM-DD format.")

    cleaned = value.strip()

    for date_format in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return DateTime.strptime(cleaned, date_format).date()
        except ValueError:
            pass

    raise ValueError("Date must use YYYY-MM-DD, for example 2024-11-01.")


ApiDate = Annotated[Date, BeforeValidator(parse_api_date)]
