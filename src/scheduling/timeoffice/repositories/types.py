from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, StrictFloat, StrictInt


class TimeOfficeSourceRow(BaseModel):
    """Base class for validated TimeOffice SQL result rows."""

    model_config = ConfigDict(extra="forbid", frozen=True)


def none_if_blank(value: Any) -> Any | None:
    if value is None:
        return None

    if isinstance(value, str) and not value.strip():
        return None

    return value


def clean_text(value: Any) -> str | None:
    value = none_if_blank(value)
    if value is None:
        return None

    cleaned = str(value).strip()
    return cleaned or None


CleanText = Annotated[str, BeforeValidator(clean_text)]
CleanNullableText = Annotated[str | None, BeforeValidator(clean_text)]

SourceInt = StrictInt
SourceNullableInt = Annotated[StrictInt | None, BeforeValidator(none_if_blank)]

SourceFloat = StrictFloat
SourceNullableFloat = Annotated[StrictFloat | None, BeforeValidator(none_if_blank)]
