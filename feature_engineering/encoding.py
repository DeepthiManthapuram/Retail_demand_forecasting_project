"""
encoding.py
===========
Categorical encoding utilities for store and item identifiers.

Two strategies are provided:
    1. LabelEncoding   — integer 0-based labels (default, lightweight)
    2. TargetEncoding  — replace category with its mean target value
                         (reduces cardinality bias for tree models)

Encoders are saved as pickle files so the same mapping is applied
consistently during inference.
"""

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.logging_config import get_logger
from utils.helpers import save_pickle, load_pickle

logger = get_logger(__name__)


class StoreItemEncoder:
    """
    Encodes ``store`` and ``item`` columns using label encoding.

    Attributes:
        store_encoder: Fitted LabelEncoder for store IDs.
        item_encoder:  Fitted LabelEncoder for item IDs.
        is_fitted:     True once fit() has been called.

    Example::

        enc = StoreItemEncoder()
        df  = enc.fit_transform(df)
        df_inf = enc.transform(df_inference)
    """

    def __init__(self) -> None:
        """Initialise encoder objects."""
        self.store_encoder: LabelEncoder = LabelEncoder()
        self.item_encoder:  LabelEncoder = LabelEncoder()
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame) -> "StoreItemEncoder":
        """
        Learn the label encoding mapping from the training set.

        Args:
            df: DataFrame containing 'store' and 'item' columns.

        Returns:
            Self (for method chaining).
        """
        self.store_encoder.fit(df["store"].unique())
        self.item_encoder.fit(df["item"].unique())
        self.is_fitted = True
        logger.debug(
            "StoreItemEncoder fitted — %d stores, %d items.",
            len(self.store_encoder.classes_),
            len(self.item_encoder.classes_),
        )
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply label encoding to a DataFrame.

        Args:
            df: DataFrame to encode (must contain 'store' and 'item').

        Returns:
            Copy with 'store_enc' and 'item_enc' columns added.

        Raises:
            RuntimeError: if fit() has not been called first.
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit() before transform().")

        df = df.copy()
        df["store_enc"] = self.store_encoder.transform(df["store"])
        df["item_enc"]  = self.item_encoder.transform(df["item"])
        return df

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fit and transform in one call."""
        return self.fit(df).transform(df)

    def save(self, path: Path) -> None:
        """Persist the encoder to disk."""
        save_pickle(self, path)
        logger.info("StoreItemEncoder saved: %s", path)

    @classmethod
    def load(cls, path: Path) -> "StoreItemEncoder":
        """Load a previously saved encoder from disk."""
        enc = load_pickle(path)
        logger.info("StoreItemEncoder loaded: %s", path)
        return enc


class TargetEncoder:
    """
    Replaces a categorical column with the mean of the target variable
    computed on the training data.

    Handles unseen categories gracefully by falling back to the global mean.

    Args:
        target_col:  Name of the target column to compute means from.
        smoothing:   Bayesian smoothing strength (higher = more regularisation).
    """

    def __init__(self, target_col: str = "sales", smoothing: float = 10.0) -> None:
        """Initialise with target column and smoothing parameter."""
        self.target_col  = target_col
        self.smoothing   = smoothing
        self._maps:   dict[str, dict] = {}      # col → {category: encoded_value}
        self._global_mean: float = 0.0
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame, cols: list[str]) -> "TargetEncoder":
        """
        Learn per-category target means with Bayesian smoothing.

        Args:
            df:   Training DataFrame containing target and categorical columns.
            cols: List of categorical column names to encode.

        Returns:
            Self.
        """
        self._global_mean = float(df[self.target_col].mean())

        for col in cols:
            stats = df.groupby(col)[self.target_col].agg(["mean", "count"])
            # Bayesian smoothing: blend category mean with global mean
            smooth = (
                (stats["count"] * stats["mean"] + self.smoothing * self._global_mean)
                / (stats["count"] + self.smoothing)
            )
            self._maps[col] = smooth.to_dict()

        self.is_fitted = True
        logger.debug("TargetEncoder fitted on columns: %s", cols)
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply target encoding.

        Args:
            df: DataFrame to encode.

        Returns:
            Copy with new '{col}_te' columns.
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit() before transform().")

        df = df.copy()
        for col, mapping in self._maps.items():
            df[f"{col}_te"] = df[col].map(mapping).fillna(self._global_mean)
        return df

    def fit_transform(self, df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
        """Fit and transform in one call."""
        return self.fit(df, cols).transform(df)

    def save(self, path: Path) -> None:
        """Persist the encoder to disk."""
        save_pickle(self, path)

    @classmethod
    def load(cls, path: Path) -> "TargetEncoder":
        """Load a saved encoder from disk."""
        return load_pickle(path)
