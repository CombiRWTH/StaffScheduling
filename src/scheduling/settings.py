from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    log_level: str = Field(default="INFO")

    # TimeOffice Database
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_server: str
    db_name: str
    db_user: str
    db_password: SecretStr


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load application settings from environment variables and .env files."""
    return Settings()  # type: ignore[call-arg]
