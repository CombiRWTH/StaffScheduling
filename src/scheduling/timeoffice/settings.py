from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TimeOfficeSettings(BaseSettings):
    """Settings for TimeOffice data transfer."""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_server: str
    db_name: str
    db_user: str
    db_password: SecretStr

    enable_cache: bool = True
    cache_root: Path = Path(".cache/timeoffice")

    jump_pool_station_ids: tuple[int, ...] = Field(default_factory=tuple)


def load_settings() -> TimeOfficeSettings:
    """Load TimeOffice settings from environment variables and .env files."""
    return TimeOfficeSettings()  # type: ignore[call-arg]
