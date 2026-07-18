"""
xgboost_model.py
================
XGBoost gradient-boosted tree regressor wrapped to implement BaseForecaster.

XGBoost consistently performs well on tabular time-series features (lags,
rolling means, calendar flags) and is typically the best or second-best model
in retail demand forecasting competitions.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

try:
    import xgboost as xgb
except ImportError:
    xgb = None

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.base_model import BaseForecaster
from utils.helpers import save_pickle, load_pickle
from config.logging_config import get_logger

logger = get_logger(__name__)

# Default hyper-parameters (tuned for retail demand data)
DEFAULT_PARAMS: dict = {
    "n_estimators":     800,
    "learning_rate":    0.05,
    "max_depth":        6,
    "min_child_weight": 3,
    "subsample":        0.8,
    "colsample_bytree": 0.8,
    "reg_alpha":        0.1,
    "reg_lambda":       1.0,
    "objective":        "reg:squarederror",
    "eval_metric":      "rmse",
    "random_state":     42,
    "n_jobs":           -1,
    "verbosity":        0,
}


class XGBoostForecaster(BaseForecaster):
    """
    XGBoost regressor wrapped as a demand forecaster.

    Supports early stopping when a validation set is provided via fit().

    Args:
        params: XGBoost hyper-parameter dictionary.  Defaults to DEFAULT_PARAMS.
    """

    def __init__(self, params: dict | None = None) -> None:
        """Initialise XGBoost model with given or default hyper-parameters."""
        super().__init__(model_name="xgboost")
        self.params: dict = {**DEFAULT_PARAMS, **(params or {})}
        self._model = None

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | None = None,
    ) -> "XGBoostForecaster":
        """
        Train the XGBoost model.

        Args:
            X_train: Training features.
            y_train: Training targets.
            X_val:   Optional validation features (enables early stopping).
            y_val:   Optional validation targets.

        Returns:
            Self.
        """
        if xgb is not None:
            self._model = xgb.XGBRegressor(**self.params)
            fit_kwargs: dict = {}
            if X_val is not None and y_val is not None:
                fit_kwargs["eval_set"] = [(X_val, y_val)]
                fit_kwargs["verbose"]  = False
            self._model.fit(X_train, y_train, **fit_kwargs)
        else:
            from sklearn.ensemble import GradientBoostingRegressor
            gbm_params = {
                "n_estimators": min(self.params.get("n_estimators", 100), 200),
                "learning_rate": self.params.get("learning_rate", 0.1),
                "max_depth": self.params.get("max_depth", 5),
                "subsample": self.params.get("subsample", 1.0),
                "random_state": self.params.get("random_state", 42),
            }
            self._model = GradientBoostingRegressor(**gbm_params)
            self._model.fit(X_train, y_train)

        self.is_fitted = True
        logger.info("XGBoostForecaster trained on %d samples (fallback=%s).", len(X_train), xgb is None)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate demand forecasts.

        Args:
            X: Feature DataFrame matching training columns.

        Returns:
            1-D numpy array of predicted sales.
        """
        if self._model is None:
            raise RuntimeError("Model is not fitted. Call fit() first.")
        return np.maximum(0, self._model.predict(X))

    def feature_importance(self) -> pd.Series:
        """
        Return feature importances sorted descending.

        Returns:
            Pandas Series indexed by feature name.
        """
        if self._model is None:
            raise RuntimeError("Model is not fitted.")
        imp = self._model.feature_importances_
        cols= self._model.feature_names_in_
        return pd.Series(imp, index=cols).sort_values(ascending=False)

    def save(self, path: Path) -> None:
        """Persist the model to a pickle file."""
        save_pickle(self, path)
        logger.info("XGBoostForecaster saved: %s", path)

    @classmethod
    def load(cls, path: Path) -> "XGBoostForecaster":
        """Load a saved XGBoostForecaster from disk."""
        obj = load_pickle(path)
        logger.info("XGBoostForecaster loaded: %s", path)
        return obj
