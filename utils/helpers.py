"""
helpers.py
==========
General-purpose utility functions used across the entire application.
Anything that does not belong to a specific domain lives here.
"""

import hashlib
import json
import os
import pickle
import sys
import time
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Generator

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.logging_config import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Timing context manager
# ---------------------------------------------------------------------------
@contextmanager
def timer(label: str = "Operation") -> Generator[None, None, None]:
    """
    Context manager that logs the elapsed time of a block.

    Args:
        label: Human-readable name for the timed block.

    Example::

        with timer("Model training"):
            model.fit(X, y)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info("%s completed in %.3f s", label, elapsed)


# ---------------------------------------------------------------------------
# Model persistence helpers
# ---------------------------------------------------------------------------
def save_pickle(obj: Any, path: Path) -> None:
    """
    Serialise an arbitrary Python object to a pickle file.

    Args:
        obj:  Object to serialise (model, scaler, encoder, etc.).
        path: Destination file path (.pkl).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(obj, fh, protocol=pickle.HIGHEST_PROTOCOL)
    logger.debug("Saved pickle: %s (%d bytes)", path, path.stat().st_size)


def load_pickle(path: Path) -> Any:
    """
    Deserialise a pickle file.

    Args:
        path: Path to the .pkl file.

    Returns:
        The deserialised Python object.

    Raises:
        FileNotFoundError: if the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Pickle file not found: {path}")
    with open(path, "rb") as fh:
        obj = pickle.load(fh)  # noqa: S301
    logger.debug("Loaded pickle: %s", path)
    return obj


def save_json(data: dict | list, path: Path) -> None:
    """
    Save a dictionary or list as a pretty-printed JSON file.

    Args:
        data: JSON-serialisable object.
        path: Destination file path (.json).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)
    logger.debug("Saved JSON: %s", path)


def load_json(path: Path) -> dict | list:
    """
    Load a JSON file.

    Args:
        path: Path to the .json file.

    Returns:
        Parsed Python object.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------
def generate_future_dates(start: date, horizon: int) -> list[date]:
    """
    Generate a list of consecutive future dates starting the day after 'start'.

    Args:
        start:   Reference date (last known date in the historical series).
        horizon: Number of future days to generate.

    Returns:
        List of date objects of length ``horizon``.
    """
    return [start + timedelta(days=i + 1) for i in range(horizon)]


def date_to_str(d: date | datetime) -> str:
    """Convert a date or datetime to ISO-8601 string (YYYY-MM-DD)."""
    if isinstance(d, datetime):
        return d.strftime("%Y-%m-%d")
    return d.strftime("%Y-%m-%d")


def str_to_date(s: str) -> date:
    """Parse an ISO-8601 date string to a date object."""
    return datetime.strptime(s, "%Y-%m-%d").date()


# ---------------------------------------------------------------------------
# Array / DataFrame helpers
# ---------------------------------------------------------------------------
def enforce_min_zero(arr: np.ndarray) -> np.ndarray:
    """
    Clip an array to ensure all values are >= 0.
    Useful for post-processing demand forecasts (negative demand is impossible).

    Args:
        arr: Input numpy array.

    Returns:
        Array with all negative values replaced by 0.
    """
    return np.clip(arr, a_min=0, a_max=None)


def round_to_int(arr: np.ndarray) -> np.ndarray:
    """
    Round floats to nearest integer and cast to int64.
    Converts predicted continuous demand to discrete unit counts.

    Args:
        arr: Float numpy array.

    Returns:
        Integer numpy array.
    """
    return np.round(arr).astype(np.int64)


def safe_divide(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    """
    Division that returns a fallback value instead of raising ZeroDivisionError.

    Args:
        numerator:   Value to divide.
        denominator: Value to divide by.
        fallback:    Value returned if denominator is zero.

    Returns:
        Division result or fallback.
    """
    if denominator == 0:
        return fallback
    return numerator / denominator


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------
def model_key(model_name: str, store: int, item: int) -> str:
    """
    Build a unique string key for a Store × Item × Model combination.
    Used as a filename stem and registry key.

    Args:
        model_name: Name of the forecasting model.
        store:      Store identifier.
        item:       Item identifier.

    Returns:
        String like ``'xgboost_s3_i12'``.
    """
    return f"{model_name}_s{store}_i{item}"


def file_hash(path: Path) -> str:
    """
    Compute the MD5 hash of a file (for change detection).

    Args:
        path: File to hash.

    Returns:
        Hex-encoded MD5 digest string.
    """
    md5 = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            md5.update(chunk)
    return md5.hexdigest()


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------
def generate_version_tag() -> str:
    """
    Generate a version tag based on current UTC time.

    Returns:
        String like ``'v20240716_193045'``.
    """
    return datetime.utcnow().strftime("v%Y%m%d_%H%M%S")
