"""
random_forest.py
================
Random Forest Regressor wrapped as a demand forecaster.

Random Forest is slower than gradient boosters on large datasets but
provides built-in variance estimates via individual tree predictions,
which are used to compute confidence intervals.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.base_model import BaseForecaster
from utils.helpers import save_pickle, load_pickle
from config.logging_config import get_logger

logger = get_logger(__name__)

DEFAULT_PARAMS: dict = {
    "n_estimators": 300,
    "max_depth":    None,
    "min_samples_split": 5,
    "min_samples_leaf":  2,
    "max_features": "sqrt",
    "n_jobs":       -1,
    "random_state": 42,
}


class RandomForestForecaster(BaseForecaster):
    """
    sklearn RandomForestRegressor wrapped as a demand forecaster.

    Provides prediction intervals via the percentile of individual tree outputs.

    Args:
        params: Override default hyper-parameters.
    """

    def __init__(self, params: dict | None = None) -> None:
        """Initialise with given or default hyper-parameters."""
        super().__init__(model_name="random_forest")
        self.params: dict = {**DEFAULT_PARAMS, **(params or {})}
        self._model: RandomForestRegressor | None = None

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "RandomForestForecaster":
        """
        Train the Random Forest on the given data.

        Args:
            X_train: Feature DataFrame.
            y_train: Target Series.

        Returns:
            Self.
        """
        self._model = RandomForestRegressor(**self.params)
        self._model.fit(X_train, y_train)
        self.is_fitted = True
        logger.info(
            "RandomForestForecaster trained on %d samples with %d trees.",
            len(X_train), self.params["n_estimators"],
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return mean prediction from all trees (non-negative)."""
        if self._model is None:
            raise RuntimeError("Model is not fitted.")
        return np.maximum(0, self._model.predict(X))

    def predict_interval(
        self,
        X: pd.DataFrame,
        alpha: float = 0.10,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute prediction intervals using the distribution of tree predictions.

        Args:
            X:     Feature DataFrame.
            alpha: Significance level (0.10 → 90 % interval).

        Returns:
            Tuple (lower_bound, upper_bound).
        """
        if self._model is None:
            raise RuntimeError("Model is not fitted.")

        # Collect predictions from each individual tree
        tree_preds = np.stack(
            [tree.predict(X) for tree in self._model.estimators_], axis=0
        )  # shape: (n_trees, n_samples)

        lower_pct = (alpha / 2) * 100
        upper_pct = (1 - alpha / 2) * 100

        lower = np.maximum(0, np.percentile(tree_preds, lower_pct, axis=0))
        upper = np.percentile(tree_preds, upper_pct, axis=0)
        return lower, upper

    def feature_importance(self) -> pd.Series:
        """Return feature importances as a sorted Series."""
        if self._model is None:
            raise RuntimeError("Model is not fitted.")
        imp  = self._model.feature_importances_
        cols = self._model.feature_names_in_
        return pd.Series(imp, index=cols).sort_values(ascending=False)

    def save(self, path: Path) -> None:
        """Persist to pickle."""
        save_pickle(self, path)
        logger.info("RandomForestForecaster saved: %s", path)

    @classmethod
    def load(cls, path: Path) -> "RandomForestForecaster":
        """Load from pickle."""
        obj = load_pickle(path)
        logger.info("RandomForestForecaster loaded: %s", path)
        return obj
