"""
model_registry.py
=================
Central registry that maps model name strings to their factory functions
and manages loading of the best saved model for a given Store × Item pair.

Responsibilities
----------------
- Map string names → model classes
- Instantiate models by name
- Find the best saved model file for (store, item)
- Load a model from disk given its path + model type
"""

import sys
from pathlib import Path
from typing import Optional

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.constants import (
    MODEL_NAIVE, MODEL_MOVING_AVG, MODEL_ARIMA, MODEL_SARIMA,
    MODEL_PROPHET, MODEL_RANDOM_FOREST, MODEL_XGBOOST, MODEL_LIGHTGBM,
    MODEL_LSTM, MODEL_GRU,
)
from config.settings import get_settings
from config.logging_config import get_logger
from models.base_model import BaseForecaster

logger   = get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Lazy imports — prevents heavyweight dependencies loading at startup
# ---------------------------------------------------------------------------
def _get_model_class(model_name: str):
    """
    Return the class corresponding to model_name without importing everything
    at the module level.

    Args:
        model_name: String identifier (e.g. 'xgboost').

    Returns:
        Uninstantiated model class.

    Raises:
        ValueError: if model_name is unknown.
    """
    name = model_name.lower()

    if name == MODEL_NAIVE:
        from models.naive import NaiveForecaster
        return NaiveForecaster

    if name == MODEL_MOVING_AVG:
        from models.naive import MovingAverageForecaster
        return MovingAverageForecaster

    if name in (MODEL_ARIMA, MODEL_SARIMA):
        from models.arima_model import ARIMAForecaster
        return ARIMAForecaster

    if name == MODEL_PROPHET:
        from models.prophet_model import ProphetForecaster
        return ProphetForecaster

    if name == MODEL_RANDOM_FOREST:
        from models.random_forest import RandomForestForecaster
        return RandomForestForecaster

    if name == MODEL_XGBOOST:
        from models.xgboost_model import XGBoostForecaster
        return XGBoostForecaster

    if name == MODEL_LIGHTGBM:
        from models.lightgbm_model import LightGBMForecaster
        return LightGBMForecaster

    if name == MODEL_LSTM:
        from models.lstm_model import LSTMForecaster
        return LSTMForecaster

    if name == MODEL_GRU:
        from models.gru_model import GRUForecaster
        return GRUForecaster

    raise ValueError(f"Unknown model name: '{model_name}'. Valid names: {_ALL_NAMES}")


_ALL_NAMES = [
    MODEL_NAIVE, MODEL_MOVING_AVG, MODEL_ARIMA, MODEL_SARIMA,
    MODEL_PROPHET, MODEL_RANDOM_FOREST, MODEL_XGBOOST, MODEL_LIGHTGBM,
    MODEL_LSTM, MODEL_GRU,
]


def create_model(model_name: str, **kwargs) -> BaseForecaster:
    """
    Instantiate a fresh (unfitted) forecaster by name.

    Args:
        model_name: Model identifier string.
        **kwargs:   Keyword arguments passed to the model's __init__.

    Returns:
        Unfitted BaseForecaster instance.
    """
    cls = _get_model_class(model_name)
    return cls(**kwargs)


def find_best_model_path(
    store: int,
    item: int,
    model_name: Optional[str] = None,
) -> Optional[Path]:
    """
    Search saved_models/ for the most recently saved model for a given
    Store × Item combination.

    File naming convention:
        {model_name}_s{store}_i{item}_{timestamp}.pkl

    Args:
        store:      Store code.
        item:       Item code.
        model_name: If provided, restrict search to this model type.

    Returns:
        Path to the newest matching file, or None if not found.
    """
    saved_dir = settings.saved_models_dir
    if not saved_dir.exists():
        return None

    pattern = f"*_s{store}_i{item}_*.pkl"
    candidates = list(saved_dir.glob(pattern))

    if model_name and model_name != "auto":
        candidates = [p for p in candidates if p.name.startswith(f"{model_name}_")]

    if not candidates:
        return None

    # Sort by modification time, newest first
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def load_model(path: Path, model_name: Optional[str] = None) -> BaseForecaster:
    """
    Load a serialised model from disk.

    Attempts to infer model_name from the filename if not provided.

    Args:
        path:       Full path to the .pkl file.
        model_name: Optional explicit model type name.

    Returns:
        Loaded BaseForecaster instance.

    Raises:
        FileNotFoundError: if path does not exist.
        ValueError:        if model_name cannot be inferred.
    """
    if not path.exists():
        raise FileNotFoundError(f"Model file not found: {path}")

    if model_name is None:
        # Infer from filename prefix (e.g. 'xgboost_s1_i1_v20240716.pkl')
        stem = path.stem                     # 'xgboost_s1_i1_v20240716'
        model_name = stem.split("_")[0]      # 'xgboost'
        logger.debug("Inferred model_name='%s' from filename.", model_name)

    cls = _get_model_class(model_name)
    return cls.load(path)


def list_saved_models() -> list[dict]:
    """
    Return metadata for all saved model files in saved_models/.

    Returns:
        List of dicts with keys: model_name, store, item, path, modified_at.
    """
    saved_dir = settings.saved_models_dir
    if not saved_dir.exists():
        return []

    results = []
    for pkl_file in sorted(saved_dir.glob("*.pkl")):
        parts = pkl_file.stem.split("_")
        try:
            model_name = parts[0]
            # Parse s{store} and i{item}
            store = int(next(p[1:] for p in parts if p.startswith("s") and p[1:].isdigit()))
            item  = int(next(p[1:] for p in parts if p.startswith("i") and p[1:].isdigit()))
        except (StopIteration, ValueError, IndexError):
            store, item = -1, -1

        results.append({
            "model_name":  model_name,
            "store":       store,
            "item":        item,
            "path":        str(pkl_file),
            "modified_at": pkl_file.stat().st_mtime,
        })

    return results
