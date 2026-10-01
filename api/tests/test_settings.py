from pathlib import Path

import pytest

from app.settings import Settings


def test_database_password_loads_from_secret_and_env_can_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("DB_PASSWORD", raising=False)
    (tmp_path / "db_password").write_text("test-password", encoding="utf-8")
    settings = Settings(_env_file=None, _secrets_dir=tmp_path, db_server="test", db_name="test", db_user="test")  # type: ignore[call-arg]
    assert settings.db_password.get_secret_value() == "test-password"
    assert "test-password" not in repr(settings)
    monkeypatch.setenv("DB_PASSWORD", "environment-password")
    settings = Settings(_env_file=None, _secrets_dir=tmp_path, db_server="test", db_name="test", db_user="test")  # type: ignore[call-arg]
    assert settings.db_password.get_secret_value() == "environment-password"
