"""
settings.py
===========
Application settings loaded from environment variables via Pydantic BaseSettings.
Auto-adjusts storage paths for Vercel/serverless environments.
"""

import os
import tempfile
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


_HERE = Path(__file__).resolve().parent
PROJECT_ROOT = _HERE.parent


class Settings(BaseSettings):
    """Central settings class with serverless read-only filesystem protection."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        protected_namespaces=(),
    )

    app_name: str = "Retail Demand Forecasting API"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    allowed_origins: str = "*"

    @property
    def cors_origins(self) -> list[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    database_url: str = f"sqlite:///{PROJECT_ROOT / 'database' / 'retail_demand.db'}"

    secret_key: str = "change-this-super-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    datasets_dir: Path = PROJECT_ROOT / "datasets"
    saved_models_dir: Path = PROJECT_ROOT / "saved_models"
    logs_dir: Path = PROJECT_ROOT / "logs"
    reports_dir: Path = PROJECT_ROOT / "reports"

    enable_advanced_models: bool = False
    auto_train_on_startup: bool = False
    default_forecast_horizon: int = 30
    model_cache_ttl_seconds: int = 3600

    log_level: str = "INFO"
    log_to_file: bool = True

    def ensure_dirs(self) -> None:
        """Safely ensure directories exist, redirecting to /tmp in serverless."""
        if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            tmp = Path(tempfile.gettempdir())
            self.datasets_dir = tmp / "datasets"
            self.saved_models_dir = tmp / "saved_models"
            self.logs_dir = tmp / "logs"
            self.reports_dir = tmp / "reports"
            self.log_to_file = False

        for directory in (
            self.datasets_dir,
            self.saved_models_dir,
            self.logs_dir,
            self.reports_dir,
        ):
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
