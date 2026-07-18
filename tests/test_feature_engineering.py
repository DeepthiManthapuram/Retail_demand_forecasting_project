"""
tests/test_feature_engineering.py
==================================
Unit tests for the feature engineering pipeline.
"""

import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from feature_engineering.time_features import add_time_features
from feature_engineering.lag_features import add_lag_features
from feature_engineering.rolling_features import add_rolling_features


def _make_series(n: int = 100) -> pd.DataFrame:
    dates = pd.date_range("2023-01-01", periods=n, freq="D")
    sales = np.random.randint(5, 100, size=n).astype(float)
    return pd.DataFrame({"date": dates, "sales": sales, "store": 1, "item": 1})


class TestTimeFeatures:
    def test_adds_expected_columns(self):
        df = _make_series()
        result = add_time_features(df)
        expected = ["day_of_week", "month", "week_of_year", "day_of_year", "quarter"]
        for col in expected:
            assert col in result.columns, f"Missing column: {col}"

    def test_cyclic_features_range(self):
        df = _make_series()
        result = add_time_features(df)
        assert result["sin_day_of_week"].between(-1.01, 1.01).all()
        assert result["cos_day_of_week"].between(-1.01, 1.01).all()

    def test_no_extra_rows(self):
        df = _make_series(80)
        result = add_time_features(df)
        assert len(result) == 80


class TestLagFeatures:
    def test_lag_columns_created(self):
        df = _make_series(90)
        result = add_lag_features(df, lags=[1, 7, 14])
        for lag in [1, 7, 14]:
            assert f"lag_{lag}" in result.columns

    def test_no_negative_lag(self):
        df = _make_series(90)
        result = add_lag_features(df, lags=[1])
        # After dropping NaN rows, lag_1 must always >= 0
        result = result.dropna()
        assert (result["lag_1"] >= 0).all()


class TestRollingFeatures:
    def test_rolling_columns_created(self):
        df = _make_series(90)
        result = add_rolling_features(df, windows=[7, 14])
        for w in [7, 14]:
            assert f"rolling_mean_{w}" in result.columns
            assert f"rolling_std_{w}"  in result.columns

    def test_rolling_mean_range(self):
        df = _make_series(90)
        result = add_rolling_features(df, windows=[7]).dropna()
        assert (result["rolling_mean_7"] > 0).all()
