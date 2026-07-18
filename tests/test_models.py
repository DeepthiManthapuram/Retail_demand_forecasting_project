"""
tests/test_models.py
====================
Unit tests for all forecaster model wrappers.
"""

import sys
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.naive import NaiveForecaster, MovingAverageForecaster
from models.xgboost_model import XGBoostForecaster
from models.lightgbm_model import LightGBMForecaster
from models.random_forest import RandomForestForecaster


# ---- Fixtures ----

def _make_data(n: int = 200):
    """Generate a simple synthetic series for testing."""
    dates  = pd.date_range("2023-01-01", periods=n, freq="D")
    sales  = np.random.randint(10, 80, size=n).astype(float)

    df = pd.DataFrame({
        "date":         dates,
        "sales":        sales,
        "lag_1":        np.roll(sales, 1),
        "lag_7":        np.roll(sales, 7),
        "lag_14":       np.roll(sales, 14),
        "rolling_mean_7": pd.Series(sales).rolling(7, min_periods=1).mean().values,
        "rolling_std_7":  pd.Series(sales).rolling(7, min_periods=1).std().fillna(0).values,
        "day_of_week":  dates.dayofweek,
        "month":        dates.month,
        "week_of_year": dates.isocalendar().week.astype(int).values,
    })

    X = df.drop(columns=["date", "sales"])
    y = df["sales"]
    return X, y, df


# ---- Naive Models ----

class TestNaiveForecaster:
    def test_fit_predict(self):
        X, y, _ = _make_data()
        X_train, y_train = X.iloc[:160], y.iloc[:160]
        X_test,  y_test  = X.iloc[160:], y.iloc[160:]

        model = NaiveForecaster()
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        assert len(preds) == len(X_test)
        assert all(p >= 0 for p in preds)
        assert model.is_fitted

    def test_predict_without_fit_raises(self):
        model = NaiveForecaster()
        X, _, _ = _make_data()
        with pytest.raises(RuntimeError):
            model.predict(X.iloc[:10])


class TestMovingAverageForecaster:
    def test_fit_predict(self):
        X, y, _ = _make_data()
        model = MovingAverageForecaster(window=7)
        model.fit(X.iloc[:160], y.iloc[:160])
        preds = model.predict(X.iloc[160:])

        assert len(preds) == len(X.iloc[160:])
        assert all(p >= 0 for p in preds)


# ---- ML Models ----

class TestXGBoostForecaster:
    def test_fit_predict_shape(self):
        X, y, _ = _make_data()
        model = XGBoostForecaster(params={"n_estimators": 20, "verbosity": 0})
        model.fit(X.iloc[:160], y.iloc[:160])
        preds = model.predict(X.iloc[160:])

        assert preds.shape == (40,)
        assert np.all(preds >= 0)

    def test_feature_importance_length(self):
        X, y, _ = _make_data()
        model = XGBoostForecaster(params={"n_estimators": 10, "verbosity": 0})
        model.fit(X.iloc[:160], y.iloc[:160])
        imp = model.feature_importance()

        assert len(imp) == X.shape[1]

    def test_predict_not_negative(self):
        X, y, _ = _make_data()
        model = XGBoostForecaster(params={"n_estimators": 10, "verbosity": 0})
        model.fit(X.iloc[:160], y.iloc[:160])
        preds = model.predict(X.iloc[160:])
        assert np.all(preds >= 0)


class TestLightGBMForecaster:
    def test_fit_predict(self):
        X, y, _ = _make_data()
        model = LightGBMForecaster(params={"n_estimators": 20, "verbosity": -1})
        model.fit(X.iloc[:160], y.iloc[:160])
        preds = model.predict(X.iloc[160:])

        assert preds.shape == (40,)
        assert np.all(preds >= 0)


class TestRandomForestForecaster:
    def test_fit_predict(self):
        X, y, _ = _make_data()
        model = RandomForestForecaster(params={"n_estimators": 20})
        model.fit(X.iloc[:160], y.iloc[:160])
        preds = model.predict(X.iloc[160:])

        assert preds.shape == (40,)
        assert np.all(preds >= 0)

    def test_predict_interval(self):
        X, y, _ = _make_data()
        model = RandomForestForecaster(params={"n_estimators": 20})
        model.fit(X.iloc[:160], y.iloc[:160])
        lower, upper = model.predict_interval(X.iloc[160:])

        assert lower.shape == (40,)
        assert upper.shape == (40,)
        assert np.all(upper >= lower)
