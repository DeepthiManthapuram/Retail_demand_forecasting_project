"""
lightgbm_model.py
=================
LightGBM gradient-boosted tree forecaster.

LightGBM is faster than XGBoost on large datasets and often achieves
equivalent or better accuracy on tabular time-series problems.
"""

import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.base_model import BaseForecaster
from utils.helpers import save_pickle, load_pickle
from config.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_PARAMS: dict = {
    "n_estimators":      1000,
    "learning_rate":     0.05,
    "num_leaves":        63,
    "max_depth":         -1,
    "min_child_samples": 20,
    "subsample":         0.8,
    "colsample_bytree":  0.8,
    "reg_alpha":         0.1,
    "reg_lambda":        1.0,
    "objective":         "regression",
    "metric":            "rmse",
    "random_state":      42,
    "n_jobs":            -1,
    "verbosity":         -1,
}


class LightGBMForecaster(BaseForecaster):
    """
    LightGBM regressor wrapped as a demand forecaster.

    Args:
        params: LightGBM hyper-parameter dictionary.
    """

    def __init__(self, params: dict | None = None) -> None:
        """Initialise with given or default hyper-parameters."""
        super().__init__(model_name="lightgbm")
        self.params: dict = {**DEFAULT_PARAMS, **(params or {})}
        self._model: lgb.LGBMRegressor | None = None

    def fit(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val: pd.DataFrame | None = None,
        y_val: pd.Series | None = None,
    ) -> "LightGBMForecaster":
        """
        Train LightGBM.

        Args:
            X_train: Training features.
            y_train: Training targets.
            X_val:   Validation features (enables early stopping).
            y_val:   Validation targets.

        Returns:
            Self.
        """
        callbacks = [lgb.early_stopping(50, verbose=False), lgb.log_evaluation(-1)]

        self._model = lgb.LGBMRegressor(**self.params)
        fit_kwargs: dict = {"callbacks": callbacks}
        if X_val is not None and y_val is not None:
            fit_kwargs["eval_set"] = [(X_val, y_val)]

        self._model.fit(X_train, y_train, **fit_kwargs)
        self.is_fitted = True
        logger.info("LightGBMForecaster trained on %d samples.", len(X_train))
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return non-negative demand predictions."""
        if self._model is None:
            raise RuntimeError("Model is not fitted.")
        return np.maximum(0, self._model.predict(X))

    def feature_importance(self) -> pd.Series:
        """Return feature importances as a sorted Series."""
        if self._model is None:
            raise RuntimeError("Model is not fitted.")
        imp  = self._model.feature_importances_
        cols = self._model.feature_name_
        return pd.Series(imp, index=cols).sort_values(ascending=False)

    def save(self, path: Path) -> None:
        """Persist to pickle."""
        save_pickle(self, path)
        logger.info("LightGBMForecaster saved: %s", path)

    @classmethod
    def load(cls, path: Path) -> "LightGBMForecaster":
        """Load from pickle."""
        obj = load_pickle(path)
        logger.info("LightGBMForecaster loaded: %s", path)
        return obj
