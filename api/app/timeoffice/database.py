import json
import subprocess
import sys
from typing import Any

import pyodbc
from sqlalchemy import URL, Dialect, Engine, ExceptionContext, create_engine, event, text
from sqlalchemy.pool import ConnectionPoolEntry

from app.settings import Settings, get_settings


class TimeOfficeUnavailable(RuntimeError):
    """Safe integration failure; never include SQL, credentials or driver error text."""

    def __init__(self, stage: str, message: str) -> None:
        self.stage = stage
        super().__init__(message)


def check_database_configuration(settings: Settings) -> None:
    missing = [
        name
        for name, value in (
            ("DB_SERVER", settings.db_server),
            ("DB_NAME", settings.db_name),
            ("DB_USER", settings.db_user),
            ("db_password", settings.db_password.get_secret_value()),
        )
        if not value.strip()
    ]
    if missing:
        raise TimeOfficeUnavailable("configuration", f"TimeOffice unavailable: supply {', '.join(missing)}.")
    if settings.db_driver not in pyodbc.drivers():
        raise TimeOfficeUnavailable("driver", "TimeOffice unavailable: install the configured ODBC driver.")


def create_db_engine(settings: Settings) -> Engine:
    """Create a lazy engine with bounded login/query waits and sanitized failures.

    All adapter queries share this connection boundary.
    Encryption is mandatory; the server certificate is verified unless `DB_TRUST_SERVER_CERTIFICATE` opts out.
    """
    url = URL.create(
        drivername="mssql+pyodbc",
        username=settings.db_user,
        password=settings.db_password.get_secret_value(),
        host=settings.db_server,
        port=settings.db_port,
        database=settings.db_name,
        query={
            "driver": settings.db_driver,
            "Encrypt": "yes",
            "TrustServerCertificate": "yes" if settings.db_trust_server_certificate else "no",
        },
    )
    # fast_executemany sends a multi-row INSERT (a published month) as one batch instead of a round trip per row.
    engine = create_engine(url, hide_parameters=True, pool_timeout=settings.db_timeout_seconds, fast_executemany=True)

    @event.listens_for(engine, "do_connect")
    def connect(
        _dialect: Dialect, _record: ConnectionPoolEntry, args: tuple[Any, ...], _params: dict[str, Any]
    ) -> pyodbc.Connection:
        check_database_configuration(settings)
        try:
            connection = pyodbc.connect(*args, timeout=settings.db_timeout_seconds)
        except pyodbc.Error:
            raise TimeOfficeUnavailable(
                "connection",
                "TimeOffice unavailable: check DNS/VPN, server port, login and trusted TLS certificate. "
                "Run just connectivity for staged diagnostics.",
            ) from None
        connection.timeout = settings.db_timeout_seconds
        return connection

    @event.listens_for(engine, "handle_error")
    def handle_error(_context: ExceptionContext) -> None:
        raise TimeOfficeUnavailable(
            "query", "TimeOffice query failed: check connectivity, schema and database permissions."
        ) from None

    return engine


def diagnose(settings: Settings) -> dict[str, str]:
    """Check configuration, driver, bounded DNS, encrypted login and SELECT 1 only.

    This deliberately bypasses the application queries.
    No application-table reads, provisioning or database writes are performed.
    """
    check_database_configuration(settings)
    try:
        subprocess.run(  # noqa: S603 — fixed interpreter/code; hostname and port are separate arguments
            [
                sys.executable,
                "-c",
                "import socket,sys; socket.getaddrinfo(sys.argv[1],sys.argv[2])",
                settings.db_server,
                str(settings.db_port),
            ],
            check=True,
            capture_output=True,
            timeout=settings.db_timeout_seconds,
        )
    except subprocess.CalledProcessError, subprocess.TimeoutExpired:
        raise TimeOfficeUnavailable(
            "dns", "TimeOffice unavailable: check server hostname and DNS/VPN access."
        ) from None
    engine = create_db_engine(settings)
    try:
        with engine.connect() as connection:
            if connection.scalar(text("SELECT 1")) != 1:
                raise TimeOfficeUnavailable("query", "TimeOffice diagnostic query returned an unexpected result.")
    finally:
        engine.dispose()
    return dict.fromkeys(("configuration", "driver", "dns", "connection", "query"), "passed")


if __name__ == "__main__":
    try:
        result = diagnose(get_settings())
    except TimeOfficeUnavailable as error:
        print(json.dumps({"status": "unavailable", "stage": error.stage, "detail": str(error)}))
        sys.exit(1)
    print(json.dumps({"status": "available", "checks": result}))
