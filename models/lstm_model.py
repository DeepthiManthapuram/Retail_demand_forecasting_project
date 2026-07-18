"""
lstm_model.py
=============
LSTM (Long Short-Term Memory) deep learning forecaster built with Keras / TensorFlow.

Architecture
------------
Input  → LSTM(64) → Dropout(0.2) → LSTM(32) → Dropout(0.2)
       → Dense(16, relu) → Dense(1)

The model uses a sliding-window (sequence-to-one) approach:
    - Input:  look-back window of ``seq_len`` historical sales + features
    - Output: single next-day forecast

Multi-step forecasting is achieved by recursively feeding predictions
back as inputs (iterated one-step-ahead strategy).
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from models.base_model import BaseForecaster
from config.constants import LSTM_UNITS, DL_LOOKBACK, DL_EPOCHS, DL_BATCH_SIZE, DL_DROPOUT
from config.logging_config import get_logger
from utils.helpers import save_pickle, load_pickle

logger = get_logger(__name__)


class LSTMForecaster(BaseForecaster):
    """
    LSTM-based demand forecaster.

    For training it expects a 1-D sales series (or feature array).
    Internally it constructs sliding-window (X, y) pairs.

    Args:
        seq_len:    Look-back window size in days.
        units:      LSTM cell units in first layer.
        epochs:     Maximum training epochs.
        batch_size: Mini-batch size.
        dropout:    Dropout rate applied after each LSTM layer.
    """

    def __init__(
        self,
        seq_len:    int = DL_LOOKBACK,
        units:      int = LSTM_UNITS,
        epochs:     int = DL_EPOCHS,
        batch_size: int = DL_BATCH_SIZE,
        dropout:    float = DL_DROPOUT,
    ) -> None:
        """Initialise LSTM hyper-parameters."""
        super().__init__(model_name="lstm")
        self.seq_len    = seq_len
        self.units      = units
        self.epochs     = epochs
        self.batch_size = batch_size
        self.dropout    = dropout
        self._keras_model = None
        self._scaler      = None
        self._history     = None

    def _build_model(self, n_features: int) -> None:
        """
        Construct and compile the Keras LSTM model.

        Args:
            n_features: Number of input features (last dimension of input tensor).
        """
        import tensorflow as tf
        from tensorflow.keras import layers, models  # type: ignore

        tf.random.set_seed(42)

        model = models.Sequential([
            layers.Input(shape=(self.seq_len, n_features)),
            layers.LSTM(self.units, return_sequences=True),
            layers.Dropout(self.dropout),
            layers.LSTM(self.units // 2, return_sequences=False),
            layers.Dropout(self.dropout),
            layers.Dense(16, activation="relu"),
            layers.Dense(1),
        ], name="LSTM_Demand_Forecaster")

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss="mse",
            metrics=["mae"],
        )
        self._keras_model = model
        logger.debug("LSTM model built: %s", model.summary())

    def _make_sequences(
        self,
        data: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert a time series array into overlapping (X, y) sequences.

        Args:
            data: 2-D array of shape (timesteps, n_features).
                  The last column is assumed to be the target (sales).

        Returns:
            Tuple of arrays (X, y) where:
                X.shape = (n_samples, seq_len, n_features)
                y.shape = (n_samples,)
        """
        X_list, y_list = [], []
        for i in range(len(data) - self.seq_len):
            X_list.append(data[i : i + self.seq_len, :])
            y_list.append(data[i + self.seq_len, -1])   # last col = target
        return np.array(X_list), np.array(y_list)

    def fit(self, X_train: pd.DataFrame, y_train: pd.Series) -> "LSTMForecaster":
        """
        Train the LSTM model.

        Args:
            X_train: Feature DataFrame (will be combined with y_train as last col).
            y_train: Target Series.

        Returns:
            Self.
        """
        from sklearn.preprocessing import MinMaxScaler
        from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau  # type: ignore

        # Combine features + target into single array; target is last column
        feature_arr = X_train.select_dtypes(include="number").values
        target_arr  = y_train.values.reshape(-1, 1)
        data = np.hstack([feature_arr, target_arr]).astype(np.float32)

        # Scale to [0, 1]
        self._scaler = MinMaxScaler()
        data_scaled  = self._scaler.fit_transform(data)

        X_seq, y_seq = self._make_sequences(data_scaled)
        if len(X_seq) == 0:
            logger.warning("Not enough data to create LSTM sequences (need > seq_len=%d rows).", self.seq_len)
            self.is_fitted = False
            return self

        n_features = X_seq.shape[2]
        self._build_model(n_features)

        callbacks = [
            EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True, verbose=0),
            ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=5, verbose=0),
        ]

        self._history = self._keras_model.fit(  # type: ignore
            X_seq, y_seq,
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_split=0.10,
            callbacks=callbacks,
            verbose=0,
            shuffle=False,
        )

        self.is_fitted = True
        logger.info(
            "LSTMForecaster trained — epochs=%d, final_loss=%.4f",
            len(self._history.history["loss"]),
            self._history.history["loss"][-1],
        )
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Multi-step ahead forecast using iterated one-step prediction.

        Args:
            X: Feature DataFrame (length = forecast horizon).

        Returns:
            1-D numpy array of predicted sales values.
        """
        if self._keras_model is None or not self.is_fitted:
            raise RuntimeError("LSTMForecaster is not fitted.")

        # Use the last seq_len rows that the scaler has seen as seed
        raise NotImplementedError(
            "LSTMForecaster.predict() requires the historical seed window. "
            "Call predict_from_seed(seed_window, horizon) instead."
        )

    def predict_from_seed(
        self,
        seed: np.ndarray,
        horizon: int,
        feature_placeholder: np.ndarray | None = None,
    ) -> np.ndarray:
        """
        Iterative multi-step ahead prediction starting from a seed sequence.

        Args:
            seed:    Array of shape (seq_len, n_features+1) — scaled input window.
            horizon: Number of future steps to predict.
            feature_placeholder: Future feature values shape (horizon, n_features).
                                 If None, last feature row is repeated.

        Returns:
            1-D numpy array of un-scaled predicted sales for ``horizon`` steps.
        """
        if self._keras_model is None:
            raise RuntimeError("Model not fitted.")

        n_features = seed.shape[1]
        window     = seed.copy()

        raw_preds = []
        for step in range(horizon):
            x_input = window[-self.seq_len :].reshape(1, self.seq_len, n_features)
            pred_scaled = float(self._keras_model.predict(x_input, verbose=0)[0, 0])

            # Build next row: use provided features or repeat last row
            if feature_placeholder is not None and step < len(feature_placeholder):
                next_row = np.append(feature_placeholder[step], pred_scaled)
            else:
                next_row = window[-1].copy()
                next_row[-1] = pred_scaled

            window = np.vstack([window, next_row.reshape(1, -1)])
            raw_preds.append(pred_scaled)

        # Inverse-transform only the target column
        dummy = np.zeros((horizon, n_features))
        dummy[:, -1] = raw_preds
        unscaled = self._scaler.inverse_transform(dummy)[:, -1]
        return np.maximum(0, unscaled)

    def save(self, path: Path) -> None:
        """
        Save the Keras model weights separately and pickle the wrapper.

        The Keras model is saved to ``{path}.keras`` and the wrapper
        (without _keras_model) is pickled to ``path``.
        """
        path = Path(path)
        keras_path = path.with_suffix(".keras")
        if self._keras_model is not None:
            self._keras_model.save(str(keras_path))

        keras_backup = self._keras_model
        self._keras_model = None          # pickle without the Keras object
        save_pickle(self, path)
        self._keras_model = keras_backup  # restore in-memory

        logger.info("LSTMForecaster saved: %s + %s", path, keras_path)

    @classmethod
    def load(cls, path: Path) -> "LSTMForecaster":
        """Load the wrapper and restore the Keras model from disk."""
        import tensorflow as tf  # noqa: PLC0415

        path = Path(path)
        obj  = load_pickle(path)

        keras_path = path.with_suffix(".keras")
        if keras_path.exists():
            obj._keras_model = tf.keras.models.load_model(str(keras_path))
            obj.is_fitted    = True

        logger.info("LSTMForecaster loaded: %s", path)
        return obj
