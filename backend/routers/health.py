"""
health.py  (router)
====================
GET /         — root redirect info
GET /health   — comprehensive system health check
"""

import sys
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config.settings import get_settings
from config.logging_config import get_logger
from database.connection import engine

logger   = get_logger("backend.routers.health")
settings = get_settings()
router   = APIRouter()


@router.get("/", summary="Root endpoint")
def root():
    """Return basic application information."""
    return {
        "app":         settings.app_name,
        "version":     settings.app_version,
        "environment": settings.environment,
        "docs":        "/docs",
        "health":      "/health",
    }


@router.get("/health", summary="System health check")
def health_check():
    """
    Perform a comprehensive health check of all system components.

    Checks:
        - Database connectivity
        - Dataset availability
        - Saved models directory

    Returns:
        JSON with status of each component.
    """
    checks: dict[str, str] = {}

    # Database check
    try:
        with engine.connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        logger.error("DB health check failed: %s", exc)
        checks["database"] = f"error: {exc}"

    # Dataset check
    synthetic = settings.datasets_dir / "synthetic_train.csv"
    kaggle    = settings.datasets_dir / "train.csv"
    if synthetic.exists():
        checks["dataset"] = f"synthetic ({synthetic.stat().st_size // 1024} KB)"
    elif kaggle.exists():
        checks["dataset"] = f"kaggle ({kaggle.stat().st_size // 1024} KB)"
    else:
        checks["dataset"] = "not found — run: python datasets/generate_dataset.py"

    # Saved models check
    saved_dir = settings.saved_models_dir
    n_models  = len(list(saved_dir.glob("*.pkl"))) if saved_dir.exists() else 0
    checks["saved_models"] = f"{n_models} model(s) found"

    overall = "ok" if checks["database"] == "ok" else "degraded"

    status_code = 200 if overall == "ok" else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status":  overall,
            "app":     settings.app_name,
            "version": settings.app_version,
            "checks":  checks,
        },
    )
