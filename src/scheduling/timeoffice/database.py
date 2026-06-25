import logging

from sqlalchemy import URL, Engine, create_engine

from scheduling.settings import Settings

logger = logging.getLogger(__name__)


def create_db_engine(settings: Settings) -> Engine:
    """Build the SQLAlchemy Engine for the TimeOffice SQL Server database."""
    url = URL.create(
        drivername="mssql+pyodbc",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_server,
        database=settings.db_name,
        query={
            "driver": settings.db_driver,
            "TrustServerCertificate": "yes",
        },
    )

    return create_engine(url)
