"""
settings.py
===========
Application settings loaded from environment variables via Pydantic BaseSettings.
All sensitive values (database URL, secrets) come from the environment / .env file.
Never hard-code secrets in source code.
"""

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------
# Resolve project root regardless of where the process is started from
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent       # config/
PROJECT_ROOT = _HERE.parent                   # project root


class Settings(BaseSettings):
    """
    Central settings class.
    Values are read first from environment variables, then from .env file.
    """

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Application
    # ------------------------------------------------------------------
    app_name: str = "Retail Demand Forecasting API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"    # development | staging | production

    # ------------------------------------------------------------------
    # API / Server
    # ------------------------------------------------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [o.strip() for o in self.allowed_origins.split(",")]

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    database_url: str = f"sqlite:///{PROJECT_ROOT / 'database' / 'retail_demand.db'}"
    # Example PostgreSQL: postgresql+asyncpg://user:pass@localhost:5432/retail_db

    # ------------------------------------------------------------------
    # Authentication / Security
    # ------------------------------------------------------------------
    secret_key: str = "change-this-super-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24   # 24 hours

    # ------------------------------------------------------------------
    # File paths  (resolved relative to project root)
    # ------------------------------------------------------------------
    datasets_dir: Path = PROJECT_ROOT / "datasets"
    saved_models_dir: Path = PROJECT_ROOT / "saved_models"
    logs_dir: Path = PROJECT_ROOT / "logs"
    reports_dir: Path = PROJECT_ROOT / "reports"

    # ------------------------------------------------------------------
    # Model behaviour
    # ------------------------------------------------------------------
    enable_advanced_models: bool = False   # PatchTST / Transformer
    auto_train_on_startup: bool = False    # retrain if no saved model found
    default_forecast_horizon: int = 30
    model_cache_ttl_seconds: int = 3600   # how long to keep model in RAM

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    log_level: str = "INFO"
    log_to_file: bool = True

    def ensure_dirs(self) -> None:
        """Create required directories if they do not exist."""
        for directory in (
            self.datasets_dir,
            self.saved_models_dir,
            self.logs_dir,
            self.reports_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return a cached singleton Settings instance.
    Using lru_cache means the .env file is read only once per process.
    """
    settings = Settings()
    settings.ensure_dirs()
    return settings
