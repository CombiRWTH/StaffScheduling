"""Request primitives shared by the feature routers."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Annotated, Any

from fastapi import HTTPException, Query, Request

from app.domain import InvalidSelection

Year = Annotated[int, Query(ge=2000, le=2200)]
Month = Annotated[int, Query(ge=1, le=12)]


def get_planning_source(request: Request) -> Any:
    """The planning database adapter; each router types it with the protocol it needs."""
    return request.app.state.planning_source


@contextmanager
def planning_errors(*, incomplete: str, invalid: str = "Invalid request.") -> Generator[None]:
    """Invalid requests become 422 and incomplete source data 409, each with a useful message."""
    try:
        yield
    except InvalidSelection as error:
        raise HTTPException(status_code=422, detail=invalid) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=incomplete) from error
