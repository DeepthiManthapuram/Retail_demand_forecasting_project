"""
arima_model.py
==============
ARIMA / SARIMA wrapper for univariate retail demand forecasting.

Uses statsmodels AutoARIMA-style grid search or explicit (p,d,q)(P,D,Q,s)
parameters.  Best suited for single-series forecasting.
"""

import sys
import warnings
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.base_model import BaseForecaster
from utils.helpers import save_pickle, load_pickle
from config.logging_config import get_logger

logger = get_logger(__name__)
warnings.filterwarnings("ignore")   # suppress statsmodels convergence warnings


class ARIMAForecaster(BaseForecaster):
    """
    ARIMA / SARIMA forecaster using statsmodels.

    For automatic order selection set ``auto=True``, which performs a grid
    search over common (p,d,q) combinations and picks the best by AIC.

    Args:
        order:          (p, d, q) ARIMA order.
        seasonal_order: (P, D, Q, s) seasonal component.  None = ARIMA only.
        auto:           When True, run automatic order selection.
    """

    def __init__(
        self,
        order:          tuple[int, int, int] = (1, 1, 1),
        seasonal_order: Optional[tuple[int, int, int, int]] = (1, 1, 1, 7),
        auto:           bool = False,
    ) -> None:
        """Initialise ARIMA with given or auto-selected orders."""
        name = "sarima" if seasonal_order else "arima"
        super().__init__(model_name=name)
        self.order          = order
        self.seasonal_order = seasonal_order
        self.auto           = auto
        self._fitted_model  = None
        self._train_series: Optional[pd.Series] = None

    def _auto_select_order(self, series: pd.Series) -> tuple[int, int, int]:
        """
        Simple AIC-based grid search over ARIMA(p,d,q) for p,d,q ∈ {0,1,2}.

        Args:
            series: Univariate time series.

        Returns:
            Tuple (p, d, q) minimising AIC.
        """
        from statsmodels.tsa.arima.model import ARIMA

        best_aic   = float("inf")
        best_order = (1, 1, 1)

        for p in range(3):
            for d in range(2):
                for q in range(3):
                    try:
                        fit = ARIMA(series, order=(p, d, q)).fit()
                        if fit.aic < best_aic:
                            best_aic   = fit.aic
                            best_order = (p, d, q)
                    except Exception:
                        continue

        logger.debug("Auto ARIMA selected order=%s (AIC=%.2f)", best_order, best_aic)
        return best_order

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "ARIMAForecaster":
        """
        Fit ARIMA / SARIMA to the sales series.

        Args:
            X_train: Not used (ARIMA is univariate); kept for interface compatibility.
            y_train: Target sales series.

        Returns:
            Self.
        """
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        from statsmodels.tsa.arima.model import ARIMA

        self._train_series = y_train.reset_index(drop=True)

        if self.auto:
            self.order = self._auto_select_order(self._train_series)

        if self.seasonal_order:
            model = SARIMAX(
                self._train_series,
                order=self.order,
                seasonal_order=self.seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
        else:
            model = ARIMA(self._train_series, order=self.order)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self._fitted_model = model.fit(disp=False)

        self.is_fitted = True
        logger.info(
            "ARIMAForecaster fitted: order=%s, seasonal=%s",
            self.order, self.seasonal_order,
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Forecast ``len(X)`` steps ahead.

        Args:
            X: DataFrame — only its length (horizon) is used.

        Returns:
            1-D numpy array of forecast values.
        """
        if self._fitted_model is None:
            raise RuntimeError("ARIMAForecaster is not fitted.")
        horizon  = len(X)
        forecast = self._fitted_model.forecast(steps=horizon)
        return np.maximum(0, np.asarray(forecast))

    def save(self, path: Path) -> None:
        """Persist to pickle."""
        save_pickle(self, path)
        logger.info("ARIMAForecaster saved: %s", path)

    @classmethod
    def load(cls, path: Path) -> "ARIMAForecaster":
        """Load from pickle."""
        obj = load_pickle(path)
        logger.info("ARIMAForecaster loaded: %s", path)
        return obj
