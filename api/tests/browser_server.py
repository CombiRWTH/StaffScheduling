"""Offline browser API: production HTTP/read flow with fictional SQL results."""

from time import sleep

import uvicorn
from fastapi import Request
from inspection_fixture import InspectionSource

from app.dependencies import get_timeoffice_service
from app.main import app
from app.timeoffice.database import TimeOfficeUnavailable
from app.timeoffice.service import TimeOfficeService

source = InspectionSource()


def browser_timeoffice(request: Request) -> TimeOfficeService:
    # Deliberate failure scenarios use months, avoiding test-only application routes.
    if request.query_params.get("month") == "4":
        raise TimeOfficeUnavailable(stage="connection", message="TimeOffice is unavailable; check connection.")
    if request.url.path == "/employees" and request.query_params.get("month") == "6":
        sleep(1)
    source.missing_evidence = request.query_params.get("month") == "5"
    return source.service


app.dependency_overrides[get_timeoffice_service] = browser_timeoffice

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=18080)
