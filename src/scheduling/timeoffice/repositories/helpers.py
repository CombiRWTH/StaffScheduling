from datetime import date as Date
from datetime import datetime as DateTime
from datetime import time as Time
from typing import Any


def required[T](value: T | None, *, field_name: str, context: str) -> T:
    """Return a required TimeOffice value or fail with source context."""
    if value is None:
        raise ValueError(f"Missing required TimeOffice field {field_name} for {context}.")

    return value


def clean_text(value: Any) -> str | None:
    """Normalize empty source text values to None."""
    if value is None:
        return None

    cleaned = str(value).strip()

    if not cleaned:
        return None

    return cleaned


def normalize_code(value: str) -> str:
    """Normalize TimeOffice code values for stable comparison."""
    return value.strip().upper()


def to_date(value: Any) -> Date | None:
    """Convert SQL date/datetime values to date values."""
    if value is None:
        return None

    if isinstance(value, Date) and not isinstance(value, DateTime):
        return value

    if isinstance(value, DateTime):
        return value.date()

    if hasattr(value, "date"):
        return value.date()

    raise TypeError(f"Cannot convert TimeOffice value to date: {value!r}")


def to_datetime(value: Any) -> DateTime:
    """Convert SQL datetime-like values to Python datetime."""
    if isinstance(value, DateTime):
        return value

    if hasattr(value, "to_pydatetime"):
        return value.to_pydatetime()

    raise TypeError(f"Cannot convert TimeOffice value to datetime: {value!r}")


def minute_of_day(value: DateTime | Time) -> int:
    """Return minutes after midnight."""
    return value.hour * 60 + value.minute


def to_non_negative_int(value: Any) -> int:
    """Convert nullable numeric source values to non-negative int."""
    if value is None:
        return 0

    result = int(value)

    if result < 0:
        raise ValueError(f"Expected non-negative TimeOffice integer, got {result}.")

    return result
