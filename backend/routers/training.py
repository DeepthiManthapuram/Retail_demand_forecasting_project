"""
training.py  (router)
======================
POST /api/train-model  — trigger model training for a Store × Item pair
"""

import sys
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config.constants import ML_MODELS
from config.logging_config import get_logger
from training.trainer import ModelTrainer
from utils.data_loader import load_raw_dataset, normalise_dataset, load_series

logger = get_logger("backend.routers.training")
router = APIRouter()

# Track ongoing training tasks {task_id: status}
_training_status: dict[str, dict] = {}


class TrainRequest(BaseModel):
    """Request body for POST /train-model."""
    store:  int = Field(..., ge=1, le=10,  description="Store ID (1-10)")
    item:   int = Field(..., ge=1, le=50,  description="Item ID (1-50)")
    models: list[str] = Field(
        default=["xgboost", "lightgbm", "random_forest"],
        description="List of model names to train.",
    )


class TrainResponse(BaseModel):
    """Response body for POST /train-model."""
    task_id:    str
    status:     str
    message:    str
    store:      int
    item:       int


def _run_training(task_id: str, store: int, item: int, models: list[str]) -> None:
    """
    Background task that runs the full training pipeline for one Store × Item.

    Args:
        task_id: Unique identifier for tracking status.
        store:   Store code.
        item:    Item code.
        models:  List of model names to train.
    """
    _training_status[task_id] = {"status": "running", "store": store, "item": item}
    try:
        raw    = load_raw_dataset()
        df     = normalise_dataset(raw)
        series = load_series(store, item, df=df)

        trainer = ModelTrainer(store=store, item=item, models_to_train=models)
        result  = trainer.run(series)

        _training_status[task_id] = {
            "status":     "completed",
            "store":      store,
            "item":       item,
            "best_model": result.get("best_model"),
            "comparison": result.get("comparison", []),
        }
        logger.info("Training task %s completed.", task_id)
    except Exception as exc:
        logger.error("Training task %s failed: %s", task_id, exc, exc_info=True)
        _training_status[task_id] = {
            "status":  "failed",
            "store":   store,
            "item":    item,
            "error":   str(exc),
        }


@router.post("/train-model", response_model=TrainResponse, summary="Trigger model training")
def train_model(
    request: TrainRequest,
    background_tasks: BackgroundTasks,
):
    """
    Launch asynchronous model training for the given Store × Item combination.

    Training runs in a background task so the API returns immediately.
    Poll GET /api/train-status/{task_id} to check progress.

    Args:
        request:          Training parameters.
        background_tasks: FastAPI background task runner.

    Returns:
        TrainResponse with task_id for status polling.
    """
    # Validate model names
    invalid = [m for m in request.models if m not in ML_MODELS]
    if invalid:
        raise HTTPException(
            status_code=422,
            detail=f"Unknown model(s): {invalid}. Valid: {ML_MODELS}",
        )

    task_id = f"s{request.store}_i{request.item}_{len(_training_status)}"
    background_tasks.add_task(
        _run_training, task_id, request.store, request.item, request.models
    )

    logger.info("Training task %s queued — store=%d, item=%d", task_id, request.store, request.item)
    return TrainResponse(
        task_id=task_id,
        status="queued",
        message=f"Training started in background. Poll /api/train-status/{task_id}.",
        store=request.store,
        item=request.item,
    )


@router.get("/train-status/{task_id}", summary="Check training task status")
def train_status(task_id: str):
    """
    Return the current status of a training task.

    Args:
        task_id: Task identifier returned by POST /train-model.

    Returns:
        Status dictionary (status, best_model, comparison, etc.).
    """
    if task_id not in _training_status:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")
    return _training_status[task_id]
