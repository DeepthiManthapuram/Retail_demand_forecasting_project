"""
lag_features.py
===============
Creates lag features for the target variable (sales).

Lag features shift the sales column backwards in time so the model can
"see" what happened 1, 7, 14 and 30 days ago.

IMPORTANT: Lags are computed *within* each Store × Item group to avoid
           information leaking from one series into another.
"""

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.constants import LAG_SIZES
from config.logging_config import get_logger

logger = get_logger(__name__)


def add_lag_features(
    df: pd.DataFrame,
    target_col: str = "sales",
    lag_sizes: list[int] | None = None,
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """
    Add lag features for the target column within each time series group.

    Args:
        df:          DataFrame sorted chronologically within groups.
        target_col:  Column whose lags are computed (default ``'sales'``).
        lag_sizes:   List of integer lag periods (default: [1, 7, 14, 30]).
        group_cols:  Columns that define a unique time series (default: ['store','item']).

    Returns:
        Copy of ``df`` with lag columns appended.
    """
    df = df.copy()
    lag_sizes   = lag_sizes or LAG_SIZES
    group_cols  = group_cols or ["store", "item"]

    for lag in lag_sizes:
        col_name = f"lag_{lag}"
        df[col_name] = (
            df.groupby(group_cols)[target_col]
              .shift(lag)
        )
        logger.debug("Added lag feature: %s", col_name)

    return df


LAG_FEATURE_COLS = [f"lag_{lag}" for lag in LAG_SIZES]
