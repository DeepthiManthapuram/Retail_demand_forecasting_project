"""
prophet_model.py
================
Facebook / Meta Prophet wrapper for seasonal demand forecasting.

Prophet is excellent at capturing yearly and weekly seasonality plus
holiday effects without extensive feature engineering.  It accepts a
simple DataFrame with columns 'ds' (date) and 'y' (sales).

Additional regressors (promotion, temperature, etc.) are added when present.
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.base_model import BaseForecaster
from utils.helpers import save_pickle, load_pickle
from config.logging_config import get_logger

logger = get_logger(__name__)

# Suppress Prophet's verbose Stan output
warnings.filterwarnings("ignore", message=".*Stan.*")


class ProphetForecaster(BaseForecaster):
    """
    Prophet wrapper for retail demand forecasting.

    Prophet handles:
        - Yearly seasonality (Fourier series, order 10)
        - Weekly seasonality
        - Indian public holiday effects
        - External regressors (promotion, temperature)

    Prediction generates future dates internally — the feature matrix X
    passed to predict() is used only to extract its length (horizon).

    Args:
        country_holidays: Country code for built-in holiday list (default 'IN').
        seasonality_mode: 'additive' or 'multiplicative'.
    """

    def __init__(
        self,
        country_holidays: str = "IN",
        seasonality_mode: str = "multiplicative",
    ) -> None:
        """Initialise Prophet with Indian holidays and multiplicative seasonality."""
        super().__init__(model_name="prophet")
        self.country_holidays  = country_holidays
        self.seasonality_mode  = seasonality_mode
        self._model            = None
        self._last_date: pd.Timestamp | None = None
        self._regressors: list[str] = []

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "ProphetForecaster":
        """
        Train Prophet.

        Expects X_train to contain a 'date' column (or datetime index).
        Optional extra regressors: 'promotion', 'temperature', 'holiday'.

        Args:
            X_train: Feature DataFrame with at least a date column.
            y_train: Target sales Series.

        Returns:
            Self.
        """
        try:
            from prophet import Prophet  # lazy import to speed up startup
        except ImportError:
            raise ImportError("Prophet not installed. Run: pip install prophet")

        # Build prophet-format DataFrame
        if "date" in X_train.columns:
            ds = pd.to_datetime(X_train["date"])
        else:
            ds = pd.to_datetime(X_train.index)

        prophet_df = pd.DataFrame({"ds": ds, "y": y_train.values})

        # Identify available extra regressors
        optional_regressors = ["promotion", "temperature", "holiday"]
        self._regressors = [r for r in optional_regressors if r in X_train.columns]
        for reg in self._regressors:
            prophet_df[reg] = X_train[reg].values

        # Initialise and configure Prophet
        self._model = Prophet(
            seasonality_mode=self.seasonality_mode,
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            interval_width=0.90,
        )

        # Add Indian public holidays
        try:
            self._model.add_country_holidays(country_name=self.country_holidays)
        except Exception:
            logger.warning("Could not add country holidays for '%s'.", self.country_holidays)

        # Register extra regressors
        for reg in self._regressors:
            self._model.add_regressor(reg)

        # Fit
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._model.fit(prophet_df)

        self._last_date = ds.max()
        self.is_fitted  = True
        logger.info("ProphetForecaster trained on %d samples.", len(prophet_df))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate forecasts for a future horizon.

        If X contains a 'date' column those dates are used; otherwise the
        next len(X) days after the last training date are used.

        Args:
            X: Feature DataFrame (date column used if present).

        Returns:
            1-D numpy array of predicted sales.
        """
        if self._model is None:
            raise RuntimeError("ProphetForecaster is not fitted.")

        horizon = len(X)

        if "date" in X.columns:
            future_ds = pd.to_datetime(X["date"])
        else:
            future_ds = pd.date_range(
                start=self._last_date + pd.Timedelta(days=1),
                periods=horizon,
                freq="D",
            )

        future_df = pd.DataFrame({"ds": future_ds})
        for reg in self._regressors:
            if reg in X.columns:
                future_df[reg] = X[reg].values
            else:
                future_df[reg] = 0   # default for missing regressors

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            forecast = self._model.predict(future_df)

        return np.maximum(0, forecast["yhat"].values)

    def predict_interval(
        self,
        X: pd.DataFrame,
        alpha: float = 0.10,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Return Prophet's built-in uncertainty interval.

        Prophet returns 'yhat_lower' and 'yhat_upper' at the configured
        ``interval_width`` (90 %).

        Args:
            X:     Feature DataFrame.
            alpha: Ignored — Prophet's interval_width is used instead.

        Returns:
            Tuple (lower_bound, upper_bound).
        """
        if self._model is None:
            raise RuntimeError("ProphetForecaster is not fitted.")

        if "date" in X.columns:
            future_ds = pd.to_datetime(X["date"])
        else:
            future_ds = pd.date_range(
                start=self._last_date + pd.Timedelta(days=1),
                periods=len(X),
                freq="D",
            )

        future_df = pd.DataFrame({"ds": future_ds})
        for reg in self._regressors:
            future_df[reg] = X[reg].values if reg in X.columns else 0

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            forecast = self._model.predict(future_df)

        lower = np.maximum(0, forecast["yhat_lower"].values)
        upper = forecast["yhat_upper"].values
        return lower, upper

    def save(self, path: Path) -> None:
        """Persist to pickle."""
        save_pickle(self, path)
        logger.info("ProphetForecaster saved: %s", path)

    @classmethod
    def load(cls, path: Path) -> "ProphetForecaster":
        """Load from pickle."""
        obj = load_pickle(path)
        logger.info("ProphetForecaster loaded: %s", path)
        return obj
