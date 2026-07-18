"""
time_features.py
================
Extracts calendar / time-based features from a datetime column.

Features generated
------------------
- year, month, quarter, week_of_year, day_of_month
- day_of_week (0=Mon … 6=Sun)
- day_of_year
- weekend         (1 if Sat/Sun else 0)
- season          (1=Winter 2=Spring 3=Summer 4=Autumn)
- month_sin / month_cos  — cyclical encoding of month
- dow_sin / dow_cos      — cyclical encoding of day-of-week
- is_month_start / is_month_end
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.constants import SEASON_MAP
from config.logging_config import get_logger

logger = get_logger(__name__)


def add_time_features(df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
    """
    Add all calendar / time-based feature columns to the DataFrame.

    Args:
        df:       Input DataFrame. Must contain a datetime column.
        date_col: Name of the datetime column (default ``'date'``).

    Returns:
        Copy of ``df`` with new feature columns appended.
    """
    df = df.copy()

    if not pd.api.types.is_datetime64_any_dtype(df[date_col]):
        df[date_col] = pd.to_datetime(df[date_col])

    dt = df[date_col].dt

    # ---- Basic calendar fields ----
    df["year"]          = dt.year
    df["month"]         = dt.month
    df["quarter"]       = dt.quarter
    df["week_of_year"]  = dt.isocalendar().week.astype(int)
    df["day_of_month"]  = dt.day
    df["day_of_week"]   = dt.dayofweek       # 0=Mon, 6=Sun
    df["day_of_year"]   = dt.dayofyear

    # ---- Weekend flag ----
    df["weekend"]       = (dt.dayofweek >= 5).astype(int)

    # ---- Season (numeric: 1=Winter, 2=Spring, 3=Summer, 4=Autumn) ----
    season_str_map = {
        "Winter": 1, "Spring": 2, "Summer": 3, "Autumn": 4,
    }
    df["season"] = df["month"].map(SEASON_MAP).map(season_str_map)

    # ---- Cyclical encoding — prevents the model treating Dec→Jan as large gap ----
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["dow_sin"]   = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]   = np.cos(2 * np.pi * df["day_of_week"] / 7)
    df["doy_sin"]   = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"]   = np.cos(2 * np.pi * df["day_of_year"] / 365)

    # ---- Month boundary flags ----
    df["is_month_start"] = dt.is_month_start.astype(int)
    df["is_month_end"]   = dt.is_month_end.astype(int)

    logger.debug("Time features added: %d new columns.", 15)
    return df


TIME_FEATURE_COLS = [
    "year", "month", "quarter", "week_of_year", "day_of_month",
    "day_of_week", "day_of_year", "weekend", "season",
    "month_sin", "month_cos", "dow_sin", "dow_cos",
    "doy_sin", "doy_cos", "is_month_start", "is_month_end",
]
