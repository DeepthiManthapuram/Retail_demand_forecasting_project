"""
forecast.py  (router)
======================
POST /api/predict           — generate a demand forecast
GET  /api/forecast-history  — list past forecasts
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from backend.schemas.forecast import PredictRequest, PredictResponse, ForecastHistoryItem
from database.connection import get_db
from database.models import Forecast, Store, Product, PredictionLog, User
from backend.routers.auth import get_optional_current_user
from prediction.predictor import DemandPredictor
from config.constants import FORECAST_HORIZONS, ALL_MODELS, MODEL_AUTO
from config.logging_config import get_logger

logger    = get_logger("backend.routers.forecast")
router    = APIRouter()
_predictor = DemandPredictor()   # singleton — loads data once


@router.post("/predict", response_model=PredictResponse, summary="Generate demand forecast")
def predict(
    request: PredictRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Generate a multi-step demand forecast for a Store × Item pair.

    Args:
        request: Validated prediction request (store, item, horizon, model).
        db:      Injected database session.

    Returns:
        PredictResponse with forecast dates, values, and confidence intervals.

    Raises:
        422: Validation error (invalid store / item / horizon).
        404: No saved model found for the combination.
        500: Prediction engine error.
    """
    t_start = time.perf_counter()
    logger.info(
        "Predict request — store=%d, item=%d, horizon=%d, model=%s, user=%s",
        request.store, request.item, request.horizon, request.model,
        current_user.username if current_user else "anonymous"
    )

    try:
        result = _predictor.predict(
            store=request.store,
            item=request.item,
            horizon=request.horizon,
            model_name=request.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("Prediction failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction engine error: {exc}")

    response_ms = (time.perf_counter() - t_start) * 1000

    # ---- Persist to DB ----
    user_id = current_user.id if current_user else None
    forecast_id = _persist_forecast(db, request, result.to_dict(), response_ms, user_id=user_id)

    result_dict = result.to_dict()
    result_dict["response_time_ms"] = round(response_ms, 2)
    result_dict["forecast_id"] = forecast_id
    return result_dict


def _persist_forecast(
    db: Session, request, result: dict, response_ms: float, user_id: Optional[int] = None
) -> Optional[int]:
    """
    Save the forecast result and a prediction log entry to the database.

    Args:
        db:          Database session.
        request:     Original prediction request.
        result:      Prediction result dictionary.
        response_ms: Total API response time in milliseconds.
        user_id:     ID of the user who requested the forecast.
    """
    fid = None
    try:
        # Resolve FK IDs
        store_row   = db.query(Store).filter(Store.store_code == request.store).first()
        product_row = db.query(Product).filter(Product.item_code == request.item).first()

        if store_row and product_row:
            forecast = Forecast(
                user_id=user_id,
                store_id=store_row.id,
                product_id=product_row.id,
                model_name=result["model_used"],
                horizon=request.horizon,
                forecast_dates=result["forecast_dates"],
                predicted_sales=result["predicted_sales"],
                lower_bound=result["lower_bound"],
                upper_bound=result["upper_bound"],
            )
            db.add(forecast)
            db.flush() # Populate the ID
            fid = forecast.id

        log = PredictionLog(
            user_id=user_id,
            store_code=request.store,
            item_code=request.item,
            model_name=result["model_used"],
            horizon=request.horizon,
            status="success",
            response_time_ms=response_ms,
        )
        db.add(log)
        db.commit()
    except Exception as exc:
        logger.warning("Failed to persist forecast to DB: %s", exc)
        db.rollback()
    return fid


@router.get(
    "/forecast-history",
    response_model=list[ForecastHistoryItem],
    summary="List forecast history",
)
def forecast_history(
    store:  Optional[int] = Query(None, ge=1, le=10),
    item:   Optional[int] = Query(None, ge=1, le=50),
    limit:  int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Retrieve past forecast records for the current user, optionally filtered by store and item.
    """
    query = db.query(Forecast, Store, Product).join(
        Store, Forecast.store_id == Store.id
    ).join(
        Product, Forecast.product_id == Product.id
    )

    # Show all history to all users in non-auth mode

    if store is not None:
        query = query.filter(Store.store_code == store)
    if item is not None:
        query = query.filter(Product.item_code == item)

    rows = query.order_by(Forecast.created_at.desc()).limit(limit).all()

    results = []
    for forecast, store_obj, product_obj in rows:
        results.append({
            "id":           forecast.id,
            "store":        store_obj.store_code,
            "store_name":   store_obj.name,
            "item":         product_obj.item_code,
            "item_name":    product_obj.name,
            "model_used":   forecast.model_name,
            "horizon":      forecast.horizon,
            "created_at":   forecast.created_at.isoformat(),
            "avg_forecast": round(
                sum(forecast.predicted_sales) / len(forecast.predicted_sales), 1
            ) if forecast.predicted_sales else 0,
        })
    return results
