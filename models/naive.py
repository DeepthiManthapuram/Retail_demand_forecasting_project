"""
naive.py
========
Baseline forecasting models:
    1. NaiveForecaster     — repeats the last observed value
    2. MovingAverageForecaster — uses the mean of the last W observations

These are used as performance lower bounds.  Any ML/DL model that cannot
beat a naive baseline is not worth deploying.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.base_model import BaseForecaster
from utils.helpers import save_pickle, load_pickle
from config.logging_config import get_logger

logger = get_logger(__name__)


class NaiveForecaster(BaseForecaster):
    """
    Naive persistence model.

    Predicts the value of the most recent observation for every future step.
    Prediction is independent of the feature matrix X — it only uses the
    last known sales value stored during fit().
    """

    def __init__(self) -> None:
        """Initialise with a zero last-value placeholder."""
        super().__init__(model_name="naive")
        self._last_value: float = 0.0

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "NaiveForecaster":
        """
        'Train' by memorising the last observed sales value.

        Args:
            X_train: Ignored — naive model does not use features.
            y_train: Target Series whose last value is stored.

        Returns:
            Self.
        """
        self._last_value = float(y_train.iloc[-1])
        self.is_fitted   = True
        logger.debug("NaiveForecaster fitted: last_value=%.2f", self._last_value)
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Return an array filled with the last observed value.

        Args:
            X: Feature DataFrame — only its length is used.

        Returns:
            1-D numpy array of shape (len(X),) with constant predictions.
        """
        return np.full(len(X), self._last_value)

    def save(self, path: Path) -> None:
        """Serialise this model to a pickle file."""
        save_pickle(self, path)

    @classmethod
    def load(cls, path: Path) -> "NaiveForecaster":
        """Deserialise a NaiveForecaster from a pickle file."""
        return load_pickle(path)


class MovingAverageForecaster(BaseForecaster):
    """
    Simple Moving Average baseline.

    Predicts the mean of the last ``window`` observed sales values for
    all future horizons.

    Args:
        window: Number of historical days to average.  Default 7.
    """

    def __init__(self, window: int = 7) -> None:
        """
        Initialise the moving average model.

        Args:
            window: Look-back window size in days.
        """
        super().__init__(model_name="moving_average")
        self.window: int = window
        self._mean_value: float = 0.0

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "MovingAverageForecaster":
        """
        Compute and store the moving average of the last ``window`` observations.

        Args:
            X_train: Ignored.
            y_train: Target Series.

        Returns:
            Self.
        """
        tail = y_train.tail(self.window)
        self._mean_value = float(tail.mean())
        self.is_fitted   = True
        logger.debug(
            "MovingAverageForecaster fitted: window=%d, mean=%.2f",
            self.window, self._mean_value,
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Return the stored moving average for every requested time step."""
        return np.full(len(X), self._mean_value)

    def save(self, path: Path) -> None:
        """Serialise to pickle."""
        save_pickle(self, path)

    @classmethod
    def load(cls, path: Path) -> "MovingAverageForecaster":
        """Deserialise from pickle."""
        return load_pickle(path)
