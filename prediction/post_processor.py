"""
post_processor.py
=================
Post-processing functions applied to raw model predictions before returning
results to the API consumer.

Operations
----------
- Clip predictions to >= 0 (demand cannot be negative)
- Round to nearest integer (we sell whole units)
- Handle NaN / Inf values
"""

import numpy as np


def post_process(predictions: np.ndarray) -> np.ndarray:
    """
    Apply standard post-processing to a raw prediction array.

    Steps:
        1. Replace NaN / Inf with 0.
        2. Clip to [0, ∞) — demand cannot be negative.
        3. Round to the nearest integer.
        4. Cast to int64.

    Args:
        predictions: Raw float predictions from any model.

    Returns:
        Cleaned integer numpy array of the same shape.
    """
    arr = np.asarray(predictions, dtype=float)
    arr = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)
    arr = np.clip(arr, a_min=0.0, a_max=None)
    arr = np.round(arr).astype(np.int64)
    return arr
