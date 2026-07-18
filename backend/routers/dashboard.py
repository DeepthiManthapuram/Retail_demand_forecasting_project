"""
dashboard.py  (router)
=======================
GET /api/dashboard  — KPI cards + summary stats for the dashboard
GET /api/metrics    — model performance comparison table
"""

import sys
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from database.connection import get_db
from database.models import Forecast, Store, Product, PredictionLog
from models.model_registry import list_saved_models
from config.constants import NUM_STORES, NUM_ITEMS, TOTAL_SERIES
from config.logging_config import get_logger

logger = get_logger("backend.routers.dashboard")
router = APIRouter()


@router.get("/dashboard", summary="Dashboard KPI cards and summary")
def get_dashboard(db: Session = Depends(get_db)):
    """
    Return all data needed to populate the dashboard page.

    Includes:
        - KPI card values (stores, items, series, forecasts, etc.)
        - Top-selling items
        - Bottom-selling items
        - Recent forecasts
        - Model usage statistics

    Args:
        db: Database session.

    Returns:
        Dictionary with all dashboard data sections.
    """
    # ---- KPI cards ----
    total_forecasts_today = db.query(func.count(PredictionLog.id)).filter(
        func.date(PredictionLog.created_at) == func.date(func.now())
    ).scalar() or 0

    total_predictions = db.query(func.count(PredictionLog.id)).scalar() or 0

    recent_logs = db.query(PredictionLog).order_by(
        PredictionLog.created_at.desc()
    ).limit(5).all()

    # ---- Saved models ----
    saved = list_saved_models()
    model_names = list({m["model_name"] for m in saved})
    best_model  = _infer_best_model(db)

    # ---- Store / item aggregates from forecasts ----
    store_stats = _store_forecast_counts(db)
    item_stats  = _item_forecast_counts(db)

    return {
        "kpi": {
            "total_stores":          NUM_STORES,
            "total_items":           NUM_ITEMS,
            "total_series":          TOTAL_SERIES,
            "forecasts_today":       total_forecasts_today,
            "total_predictions":     total_predictions,
            "saved_models":          len(saved),
            "available_model_types": model_names,
            "best_model":            best_model,
        },
        "recent_predictions": [
            {
                "store":      log.store_code,
                "item":       log.item_code,
                "model":      log.model_name,
                "horizon":    log.horizon,
                "status":     log.status,
                "created_at": log.created_at.isoformat(),
            }
            for log in recent_logs
        ],
        "store_forecast_counts": store_stats,
        "item_forecast_counts":  item_stats,
    }


def _infer_best_model(db: Session) -> str:
    """
    Return the most commonly used model name in past forecasts.

    Args:
        db: Database session.

    Returns:
        Model name string or 'N/A' if no forecasts exist.
    """
    row = db.query(
        Forecast.model_name,
        func.count(Forecast.id).label("cnt"),
    ).group_by(Forecast.model_name).order_by(func.count(Forecast.id).desc()).first()
    return row.model_name if row else "N/A"


def _store_forecast_counts(db: Session) -> list[dict]:
    """Return forecast counts grouped by store."""
    rows = db.query(
        Store.store_code, Store.name, func.count(Forecast.id).label("forecasts")
    ).outerjoin(Forecast, Store.id == Forecast.store_id).group_by(
        Store.store_code, Store.name
    ).all()
    return [{"store": r.store_code, "name": r.name, "forecasts": r.forecasts} for r in rows]


def _item_forecast_counts(db: Session) -> list[dict]:
    """Return forecast counts grouped by item."""
    rows = db.query(
        Product.item_code, Product.name, func.count(Forecast.id).label("forecasts")
    ).outerjoin(Forecast, Product.id == Forecast.product_id).group_by(
        Product.item_code, Product.name
    ).order_by(func.count(Forecast.id).desc()).limit(20).all()
    return [{"item": r.item_code, "name": r.name, "forecasts": r.forecasts} for r in rows]


@router.get("/metrics", summary="Model performance metrics comparison")
def get_metrics():
    """
    Return all saved model metadata and their evaluation metrics
    for the Model Performance page.

    Returns:
        List of model metadata dicts sorted by RMSE.
    """
    saved = list_saved_models()
    # Sort by modification time (newest first) as proxy for "latest evaluation"
    saved.sort(key=lambda m: m["modified_at"], reverse=True)
    return {"models": saved, "count": len(saved)}
