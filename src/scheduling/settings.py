from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    log_level: str = "INFO"

    # TimeOffice Database
    db_driver: str = "ODBC Driver 18 for SQL Server"
    db_server: str
    db_name: str
    db_user: str
    db_password: SecretStr

    # Solver
    solver_max_time_seconds: float = 30
    solver_num_search_workers: int | None = None
    solver_random_seed: int | None = None
    solver_log_search_progress: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load application settings from environment variables and .env files."""
    return Settings()  # type: ignore[call-arg]
