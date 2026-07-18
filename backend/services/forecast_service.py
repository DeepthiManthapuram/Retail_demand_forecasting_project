"""
services/forecast_service.py
=============================
Business-logic service layer between the router and the prediction engine.
Keeps routers thin — all heavy lifting is here.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from prediction.predictor import DemandPredictor, PredictionResult
from config.logging_config import get_logger

logger    = get_logger("backend.services.forecast_service")
_predictor = DemandPredictor()    # singleton


def generate_forecast(
    store: int,
    item:  int,
    horizon: int,
    model:   str,
) -> PredictionResult:
    """
    Generate a demand forecast by delegating to the DemandPredictor.

    Args:
        store:   Store code (1-10).
        item:    Item code (1-50).
        horizon: Forecast horizon in days.
        model:   Model name or 'auto'.

    Returns:
        PredictionResult dataclass.
    """
    logger.info(
        "ForecastService: store=%d, item=%d, horizon=%d, model=%s",
        store, item, horizon, model,
    )
    return _predictor.predict(store=store, item=item, horizon=horizon, model_name=model)
