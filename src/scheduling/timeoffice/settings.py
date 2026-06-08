from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TimeOfficeSettings(BaseSettings):
    """Settings for TimeOffice data transfer."""

    model_config = SettingsConfigDict(extra="ignore")

    db_server: str | None = None
    db_name: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_driver: str = "ODBC Driver 18 for SQL Server"

    enable_cache: bool = True
    cache_root: Path = Path(".cache/timeoffice")

    jump_pool_station_ids: tuple[int, ...] = Field(default_factory=tuple)
