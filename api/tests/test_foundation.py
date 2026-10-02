import subprocess
from typing import cast
from unittest.mock import MagicMock

import httpx
import pyodbc
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr, ValidationError

from app.main import app
from app.settings import Settings
from app.timeoffice.database import TimeOfficeConflict, TimeOfficeUnavailable, create_db_engine, diagnose


def offline_settings(db_timeout_seconds: int = 5) -> Settings:
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        _secrets_dir=None,  # type: ignore[call-arg]
        db_server="127.0.0.1",
        db_name="test",
        db_user="test",
        db_password=SecretStr("private-test-marker"),
        db_timeout_seconds=db_timeout_seconds,
    )


def test_liveness_survives_missing_database_config(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.main as main

    settings = offline_settings()
    settings.db_password = SecretStr("")
    monkeypatch.setattr(main, "settings", settings)
    with TestClient(app) as test_client:
        client = cast(httpx.Client, test_client)
        assert client.get("/status").json() == {"status": "healthy"}
        response = client.get("/planning/options", params={"year": 2026, "month": 1})
        assert response.status_code == 503
        assert response.json()["stage"] == "configuration"
        assert "db_password" in response.json()["detail"]
        assert client.get("/status").status_code == 200


def test_shared_engine_has_verified_tls_and_sanitizes_login_and_query(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = offline_settings()
    monkeypatch.setattr(pyodbc, "drivers", lambda: [settings.db_driver])
    connect = MagicMock(side_effect=pyodbc.OperationalError("private-test-marker; login rejected"))
    monkeypatch.setattr(pyodbc, "connect", connect)
    engine = create_db_engine(settings)
    try:
        with pytest.raises(TimeOfficeUnavailable, match="trusted TLS") as caught, engine.connect():
            pass
        assert caught.value.stage == "connection"
        assert "private-test-marker" not in str(caught.value)
        connection_string = connect.call_args.args[0]
        assert "Encrypt=yes" in connection_string
        assert "TrustServerCertificate=no" in connection_string
        assert connect.call_args.kwargs["timeout"] == 5
        trusting = create_db_engine(settings.model_copy(update={"db_trust_server_certificate": True}))
        with pytest.raises(TimeOfficeUnavailable), trusting.connect():
            pass
        assert "Encrypt=yes;TrustServerCertificate=yes" in connect.call_args.args[0]
        # Invoke the same engine error boundary used by SQLAlchemy for DBAPI query failures.
        with pytest.raises(TimeOfficeUnavailable, match="permissions"):
            engine.dialect.dispatch.handle_error(MagicMock())
        # A deadlock victim or duplicate key is a rolled-back conflict, also without driver text.
        for error in (pyodbc.Error("40001", "private-test-marker deadlock"), pyodbc.IntegrityError("23000", "x")):
            with pytest.raises(TimeOfficeConflict, match="nothing was changed") as conflict:
                engine.dialect.dispatch.handle_error(MagicMock(original_exception=error))
            assert "private-test-marker" not in str(conflict.value)
    finally:
        engine.dispose()


def test_diagnostics_are_read_only_and_dispose_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.timeoffice.database as database

    settings = offline_settings()
    monkeypatch.setattr(pyodbc, "drivers", lambda: [settings.db_driver])
    dns = MagicMock()
    monkeypatch.setattr(subprocess, "run", dns)
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value.scalar.return_value = 1
    monkeypatch.setattr(database, "create_db_engine", MagicMock(return_value=engine))
    assert set(diagnose(settings).values()) == {"passed"}
    assert dns.call_args.kwargs["timeout"] == 5
    connection = engine.connect.return_value.__enter__.return_value
    assert str(connection.scalar.call_args.args[0]) == "SELECT 1"
    engine.dispose.assert_called_once()
    dns.side_effect = subprocess.TimeoutExpired("dns", 5)
    with pytest.raises(TimeOfficeUnavailable, match="DNS/VPN") as caught:
        diagnose(settings)
    assert caught.value.stage == "dns"


def test_driver_and_settings_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pyodbc, "drivers", MagicMock(return_value=[]))
    with pytest.raises(TimeOfficeUnavailable, match="ODBC") as caught:
        diagnose(offline_settings())
    assert caught.value.stage == "driver"
    with pytest.raises(ValidationError):
        offline_settings(db_timeout_seconds=0)
