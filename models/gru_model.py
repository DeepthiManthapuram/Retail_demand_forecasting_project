"""
gru_model.py
============
GRU (Gated Recurrent Unit) deep learning forecaster.

Architecture is identical to the LSTM model but uses GRU cells, which
have fewer parameters and often train faster with similar accuracy.
Shares the same sliding-window and iterative-prediction strategy as LSTMForecaster.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.lstm_model import LSTMForecaster   # reuse parent logic
from config.constants import GRU_UNITS, DL_LOOKBACK, DL_EPOCHS, DL_BATCH_SIZE, DL_DROPOUT
from config.logging_config import get_logger
from utils.helpers import save_pickle, load_pickle

logger = get_logger(__name__)


class GRUForecaster(LSTMForecaster):
    """
    GRU-based demand forecaster.

    Inherits all training, prediction, and persistence logic from
    LSTMForecaster; overrides only _build_model() to use GRU cells.

    Args:
        seq_len:    Sliding-window length.
        units:      GRU cell units.
        epochs:     Maximum training epochs.
        batch_size: Mini-batch size.
        dropout:    Dropout rate.
    """

    def __init__(
        self,
        seq_len:    int = DL_LOOKBACK,
        units:      int = GRU_UNITS,
        epochs:     int = DL_EPOCHS,
        batch_size: int = DL_BATCH_SIZE,
        dropout:    float = DL_DROPOUT,
    ) -> None:
        """Initialise GRU hyper-parameters."""
        super().__init__(
            seq_len=seq_len,
            units=units,
            epochs=epochs,
            batch_size=batch_size,
            dropout=dropout,
        )
        # Override the inherited model_name
        self.model_name = "gru"

    def _build_model(self, n_features: int) -> None:
        """
        Build the Keras GRU model.

        Args:
            n_features: Number of input features (last dimension of input tensor).
        """
        import tensorflow as tf
        from tensorflow.keras import layers, models  # type: ignore

        tf.random.set_seed(42)

        model = models.Sequential([
            layers.Input(shape=(self.seq_len, n_features)),
            layers.GRU(self.units, return_sequences=True),
            layers.Dropout(self.dropout),
            layers.GRU(self.units // 2, return_sequences=False),
            layers.Dropout(self.dropout),
            layers.Dense(16, activation="relu"),
            layers.Dense(1),
        ], name="GRU_Demand_Forecaster")

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss="mse",
            metrics=["mae"],
        )
        self._keras_model = model
        logger.debug("GRU model built.")

    def save(self, path: Path) -> None:
        """Save GRU model weights and wrapper pickle."""
        path = Path(path)
        keras_path = path.with_suffix(".keras")
        if self._keras_model is not None:
            self._keras_model.save(str(keras_path))

        keras_backup = self._keras_model
        self._keras_model = None
        save_pickle(self, path)
        self._keras_model = keras_backup
        logger.info("GRUForecaster saved: %s", path)

    @classmethod
    def load(cls, path: Path) -> "GRUForecaster":
        """Load GRU wrapper and Keras model from disk."""
        import tensorflow as tf  # noqa: PLC0415

        path = Path(path)
        obj  = load_pickle(path)

        keras_path = path.with_suffix(".keras")
        if keras_path.exists():
            obj._keras_model = tf.keras.models.load_model(str(keras_path))
            obj.is_fitted    = True

        logger.info("GRUForecaster loaded: %s", path)
        return obj
