"""
base_model.py
=============
Abstract base class for all forecasting models in the pipeline.

Every model must implement:
    - fit(X_train, y_train)
    - predict(X)
    - save(path)
    - load(path)   [class method]

Optional but encouraged:
    - predict_interval(X, alpha) — returns (lower, upper) confidence bounds
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.logging_config import get_logger

logger = get_logger(__name__)


class BaseForecaster(ABC):
    """
    Abstract base class defining the interface every forecasting model must
    implement.

    Attributes:
        model_name: Unique string identifier for the model type.
        is_fitted:  True after fit() has been called successfully.
    """

    def __init__(self, model_name: str) -> None:
        """
        Initialise the base forecaster.

        Args:
            model_name: Human-readable model identifier string.
        """
        self.model_name: str = model_name
        self.is_fitted:  bool = False

    @abstractmethod
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "BaseForecaster":
        """
        Train the model on the given feature matrix and target.

        Args:
            X_train: Feature DataFrame (rows = samples, cols = features).
            y_train: Target Series (daily sales).

        Returns:
            Self (for method chaining).
        """

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Generate predictions for the given feature matrix.

        Args:
            X: Feature DataFrame with the same columns used during fit().

        Returns:
            1-D numpy array of predicted sales values.
        """

    def predict_interval(
        self,
        X: pd.DataFrame,
        alpha: float = 0.10,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Return lower and upper prediction interval bounds.

        Default implementation: ±15 % of point estimate.
        Subclasses should override with model-specific intervals.

        Args:
            X:     Feature DataFrame.
            alpha: Significance level (0.10 = 90 % interval).

        Returns:
            Tuple (lower_bound, upper_bound) as 1-D numpy arrays.
        """
        point = self.predict(X)
        margin = point * 0.15
        return np.maximum(0, point - margin), point + margin

    @abstractmethod
    def save(self, path: Path) -> None:
        """
        Persist the trained model artefact to disk.

        Args:
            path: Destination file path.
        """

    @classmethod
    @abstractmethod
    def load(cls, path: Path) -> "BaseForecaster":
        """
        Load a trained model artefact from disk.

        Args:
            path: Source file path.

        Returns:
            Loaded forecaster instance.
        """

    def __repr__(self) -> str:
        status = "fitted" if self.is_fitted else "not fitted"
        return f"<{self.__class__.__name__} model_name={self.model_name!r} {status}>"
