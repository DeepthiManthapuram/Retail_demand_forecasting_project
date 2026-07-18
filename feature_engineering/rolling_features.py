"""
rolling_features.py
===================
Computes rolling-window and expanding statistics on the sales column.

Features generated (per window size W in ROLLING_WINDOWS)
----------------------------------------------------------
- rolling_mean_W       — average sales over past W days
- rolling_std_W        — standard deviation over past W days
- rolling_median_W     — median over past W days
- rolling_max_W        — maximum over past W days
- rolling_min_W        — minimum over past W days
- expanding_mean       — cumulative mean from series start

All statistics are computed *within* each Store × Item group using a
closed='left' window (current row excluded) to prevent data leakage.
"""

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.constants import ROLLING_WINDOWS
from config.logging_config import get_logger

logger = get_logger(__name__)


def add_rolling_features(
    df: pd.DataFrame,
    target_col: str = "sales",
    windows: list[int] | None = None,
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    """
    Add rolling-window statistics and an expanding mean to the DataFrame.

    Args:
        df:          DataFrame sorted chronologically within groups.
        target_col:  Column to compute rolling stats on (default ``'sales'``).
        windows:     List of rolling window sizes in days (default: [7, 14, 30]).
        group_cols:  Columns defining each time series group.

    Returns:
        Copy of ``df`` with rolling feature columns appended.
    """
    df = df.copy()
    windows    = windows or ROLLING_WINDOWS
    group_cols = group_cols or ["store", "item"]

    grouped = df.groupby(group_cols)[target_col]

    for w in windows:
        # Shift by 1 to avoid including the current day (data leakage)
        rolled = grouped.shift(1).groupby(
            [df[c] for c in group_cols]
        ).rolling(window=w, min_periods=1)

        # We cannot chain .rolling() after .shift() in a single groupby in
        # pandas < 2.0, so we use transform instead.
        shifted = grouped.shift(1)

        df[f"rolling_mean_{w}"]   = _rolling_transform(df, shifted, group_cols, w, "mean")
        df[f"rolling_std_{w}"]    = _rolling_transform(df, shifted, group_cols, w, "std")
        df[f"rolling_median_{w}"] = _rolling_transform(df, shifted, group_cols, w, "median")
        df[f"rolling_max_{w}"]    = _rolling_transform(df, shifted, group_cols, w, "max")
        df[f"rolling_min_{w}"]    = _rolling_transform(df, shifted, group_cols, w, "min")

    # Expanding mean (uses all past data in the series, current excluded)
    df["expanding_mean"] = (
        df.groupby(group_cols)[target_col]
          .transform(lambda s: s.shift(1).expanding(min_periods=1).mean())
    )

    logger.debug("Rolling features added for windows: %s", windows)
    return df


def _rolling_transform(
    df: pd.DataFrame,
    shifted_series: pd.Series,
    group_cols: list[str],
    window: int,
    func: str,
) -> pd.Series:
    """
    Apply a named rolling aggregation to a shifted grouped series.

    Args:
        df:             Original DataFrame (used for group keys).
        shifted_series: Pre-shifted target series aligned with df index.
        group_cols:     Grouping columns.
        window:         Rolling window size.
        func:           Aggregation name ('mean', 'std', 'median', 'max', 'min').

    Returns:
        Series of the same length as df containing the rolling statistic.
    """
    result = (
        shifted_series
        .groupby([df[c] for c in group_cols])
        .transform(lambda s: s.rolling(window=window, min_periods=1).agg(func))
    )
    return result


def get_rolling_feature_cols(windows: list[int] | None = None) -> list[str]:
    """
    Return the list of rolling feature column names for given windows.

    Args:
        windows: List of window sizes. Uses ROLLING_WINDOWS if None.

    Returns:
        Sorted list of column name strings.
    """
    windows = windows or ROLLING_WINDOWS
    cols = []
    for w in windows:
        cols.extend([
            f"rolling_mean_{w}", f"rolling_std_{w}", f"rolling_median_{w}",
            f"rolling_max_{w}", f"rolling_min_{w}",
        ])
    cols.append("expanding_mean")
    return cols
