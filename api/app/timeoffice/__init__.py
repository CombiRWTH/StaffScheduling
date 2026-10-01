"""TimeOffice adapter. Use `TimeOfficeService`; everything else in this package is internal."""

from app.timeoffice.database import TimeOfficeUnavailable, create_db_engine
from app.timeoffice.service import TimeOfficeService

__all__ = ["TimeOfficeService", "TimeOfficeUnavailable", "create_db_engine"]
