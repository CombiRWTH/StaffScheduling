from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class SchedulingBaseModel(BaseModel):
    """Base model for canonical scheduling data."""

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
PositiveId = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
MinuteOfDay = Annotated[int, Field(ge=0, lt=24 * 60)]
