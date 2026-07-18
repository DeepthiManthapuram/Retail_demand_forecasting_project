"""
metrics.py
==========
Standard regression metrics used to evaluate all forecasting models.

Metrics implemented
-------------------
- MAE   (Mean Absolute Error)
- RMSE  (Root Mean Squared Error)
- MAPE  (Mean Absolute Percentage Error)
- R²    (Coefficient of Determination)

All functions accept plain numpy arrays or pandas Series.
"""

import sys
from pathlib import Path
from typing import Union

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.logging_config import get_logger

logger = get_logger(__name__)

_Array = Union[np.ndarray, pd.Series]


def mae(y_true: _Array, y_pred: _Array) -> float:
    """
    Mean Absolute Error.

    Args:
        y_true: Observed values.
        y_pred: Predicted values.

    Returns:
        MAE as a float (lower is better).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true: _Array, y_pred: _Array) -> float:
    """
    Root Mean Squared Error.

    Args:
        y_true: Observed values.
        y_pred: Predicted values.

    Returns:
        RMSE as a float (lower is better).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.sqrt(np.mean((y_true - y_pred) ** 2)))


def mape(y_true: _Array, y_pred: _Array, epsilon: float = 1e-8) -> float:
    """
    Mean Absolute Percentage Error (expressed as a percentage, e.g. 5.2 = 5.2 %).

    Rows where y_true ≈ 0 are excluded to avoid division by zero.

    Args:
        y_true:   Observed values.
        y_pred:   Predicted values.
        epsilon:  Small constant to avoid division by near-zero values.

    Returns:
        MAPE percentage as a float (lower is better).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    mask   = np.abs(y_true) > epsilon
    if mask.sum() == 0:
        return float("nan")
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def r2_score(y_true: _Array, y_pred: _Array) -> float:
    """
    Coefficient of Determination (R²).

    Args:
        y_true: Observed values.
        y_pred: Predicted values.

    Returns:
        R² as a float (higher is better; 1.0 = perfect).
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    if ss_tot == 0:
        return float("nan")
    return float(1 - ss_res / ss_tot)


def compute_all_metrics(y_true: _Array, y_pred: _Array) -> dict[str, float]:
    """
    Compute MAE, RMSE, MAPE, and R² in a single call.

    Args:
        y_true: Observed values.
        y_pred: Predicted values.

    Returns:
        Dictionary with keys 'mae', 'rmse', 'mape', 'r2'.
    """
    return {
        "mae":  round(mae(y_true, y_pred), 4),
        "rmse": round(rmse(y_true, y_pred), 4),
        "mape": round(mape(y_true, y_pred), 4),
        "r2":   round(r2_score(y_true, y_pred), 4),
    }
