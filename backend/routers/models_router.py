"""
models_router.py
================
GET /api/model-info       — list all saved model artefacts
GET /api/model-info/{key} — details of a specific saved model
"""

import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from models.model_registry import list_saved_models
from config.constants import ALL_MODELS
from config.logging_config import get_logger

logger = get_logger("backend.routers.models_router")
router = APIRouter()


@router.get("/model-info", summary="List all saved model artefacts")
def model_info():
    """
    Return metadata for every saved model file in the saved_models/ directory.

    Returns:
        List of model metadata dicts plus available model type names.
    """
    saved = list_saved_models()
    return {
        "saved_models":       saved,
        "count":              len(saved),
        "available_types":    ALL_MODELS,
    }


@router.get("/model-info/{store}/{item}", summary="Saved models for a Store × Item")
def model_info_for_series(store: int, item: int):
    """
    Return saved model artefacts for a specific Store × Item combination.

    Args:
        store: Store code (path param).
        item:  Item code (path param).

    Returns:
        List of model metadata dicts for the given series.
    """
    all_models = list_saved_models()
    filtered   = [m for m in all_models if m["store"] == store and m["item"] == item]

    if not filtered:
        raise HTTPException(
            status_code=404,
            detail=f"No saved models found for store={store}, item={item}. "
                   "Train a model first via POST /api/train-model.",
        )
    return {"store": store, "item": item, "models": filtered}
