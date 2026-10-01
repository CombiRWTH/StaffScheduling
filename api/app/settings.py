from functools import lru_cache
from os import environ
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        secrets_dir=environ.get("SECRETS_DIR", "../.secrets"),
        extra="ignore",
    )

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # TimeOffice Database
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_server: str = ""
    db_port: int = Field(default=1433, ge=1, le=65535)
    db_name: str = ""
    db_user: str = ""
    db_password: SecretStr = SecretStr("")
    db_timeout_seconds: int = Field(default=5, ge=1, le=30)

    # Solver
    solver_max_time_seconds: float = Field(default=30, gt=0, allow_inf_nan=False)
    solver_num_search_workers: int | None = Field(default=None, ge=1)
    solver_random_seed: int | None = None
    solver_log_search_progress: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load application settings from environment variables and .env files."""
    return Settings()  # type: ignore[call-arg]
