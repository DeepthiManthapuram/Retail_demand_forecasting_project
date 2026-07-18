"""
pipeline.py  (feature_engineering)
===================================
Unified FeatureEngineeringPipeline that applies all feature-engineering
steps in the correct order.

Steps (in order)
----------------
1. Time features      (year, month, season, cyclical encodings …)
2. Lag features       (lag_1, lag_7, lag_14, lag_30)
3. Rolling features   (rolling_mean_7, rolling_std_7 … expanding_mean)
4. Store / item encoding (label encoding → store_enc, item_enc)
5. Drop NaN rows introduced by lags (only for training)

The pipeline is designed to be:
    - Reusable across train / val / test splits
    - Serialisable (save / load as pickle for inference)
    - Configurable via constructor arguments
"""

import sys
from pathlib import Path
from typing import Optional

import pandas as pd
from sklearn.preprocessing import StandardScaler

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from feature_engineering.time_features  import add_time_features, TIME_FEATURE_COLS
from feature_engineering.lag_features   import add_lag_features, LAG_FEATURE_COLS
from feature_engineering.rolling_features import (
    add_rolling_features, get_rolling_feature_cols,
)
from feature_engineering.encoding import StoreItemEncoder
from config.constants import ROLLING_WINDOWS, LAG_SIZES
from config.logging_config import get_logger
from utils.helpers import save_pickle, load_pickle

logger = get_logger(__name__)


class FeatureEngineeringPipeline:
    """
    Orchestrates all feature engineering steps for the retail demand dataset.

    Attributes:
        encoder:      StoreItemEncoder fitted on the training data.
        scaler:       Optional StandardScaler for numeric features.
        feature_cols: Final list of input feature columns produced.
        is_fitted:    True once fit_transform() has been called.

    Args:
        use_scaler:    Whether to apply StandardScaler to numeric features.
        lag_sizes:     Override default lag sizes.
        rolling_windows: Override default rolling window sizes.
    """

    def __init__(
        self,
        use_scaler: bool = False,
        lag_sizes: list[int] | None = None,
        rolling_windows: list[int] | None = None,
    ) -> None:
        """Initialise the pipeline with optional configuration overrides."""
        self.use_scaler      = use_scaler
        self.lag_sizes       = lag_sizes or LAG_SIZES
        self.rolling_windows = rolling_windows or ROLLING_WINDOWS
        self.encoder         = StoreItemEncoder()
        self.scaler: Optional[StandardScaler] = StandardScaler() if use_scaler else None
        self.feature_cols: list[str] = []
        self._scale_cols:  list[str] = []
        self.is_fitted: bool = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def fit_transform(
        self,
        df: pd.DataFrame,
        target_col: str = "sales",
        drop_na: bool = True,
    ) -> pd.DataFrame:
        """
        Fit the pipeline on training data and return the feature DataFrame.

        Args:
            df:         Normalised training DataFrame.
            target_col: Name of the sales / target column.
            drop_na:    If True, drop rows where any lag/rolling value is NaN.

        Returns:
            Transformed DataFrame with all feature columns and the target.
        """
        logger.info("FeatureEngineeringPipeline: fit_transform started …")

        # Step 1: time features
        df = add_time_features(df)

        # Step 2: lag features
        df = add_lag_features(df, target_col=target_col, lag_sizes=self.lag_sizes)

        # Step 3: rolling features
        df = add_rolling_features(df, target_col=target_col, windows=self.rolling_windows)

        # Step 4: store / item encoding
        df = self.encoder.fit_transform(df)

        # Step 5: drop NaN rows (from lags)
        if drop_na:
            before = len(df)
            df = df.dropna(subset=self._get_lag_cols() + self._get_rolling_cols()).reset_index(drop=True)
            logger.info("Dropped %d NaN rows after lag/rolling computation.", before - len(df))

        # Step 6: optional scaling
        self._scale_cols = self._get_numeric_scale_cols(df)
        if self.use_scaler and self.scaler is not None:
            df[self._scale_cols] = self.scaler.fit_transform(df[self._scale_cols])

        self.feature_cols = self._build_feature_list(df, target_col)
        self.is_fitted    = True
        logger.info("fit_transform complete. Features: %d", len(self.feature_cols))
        return df

    def transform(
        self,
        df: pd.DataFrame,
        target_col: str = "sales",
        drop_na: bool = False,
    ) -> pd.DataFrame:
        """
        Apply fitted pipeline to new data (validation / test / inference).

        Args:
            df:         DataFrame to transform (need not contain target_col).
            target_col: Name of the sales column (if present).
            drop_na:    Whether to drop NaN rows.

        Returns:
            Transformed DataFrame.

        Raises:
            RuntimeError: if fit_transform() was not called first.
        """
        if not self.is_fitted:
            raise RuntimeError("Call fit_transform() before transform().")

        df = add_time_features(df)
        df = add_lag_features(df, target_col=target_col, lag_sizes=self.lag_sizes)
        df = add_rolling_features(df, target_col=target_col, windows=self.rolling_windows)
        df = self.encoder.transform(df)

        if drop_na:
            df = df.dropna(subset=self._get_lag_cols()).reset_index(drop=True)

        if self.use_scaler and self.scaler is not None:
            existing_cols = [c for c in self._scale_cols if c in df.columns]
            df[existing_cols] = self.scaler.transform(df[existing_cols])

        return df

    def get_feature_matrix(
        self,
        df: pd.DataFrame,
        target_col: str = "sales",
    ) -> tuple[pd.DataFrame, pd.Series]:
        """
        Extract the feature matrix X and target vector y from a transformed DataFrame.

        Args:
            df:         Transformed DataFrame (output of fit_transform or transform).
            target_col: Name of the target column.

        Returns:
            Tuple (X, y) where X is the feature DataFrame and y is the target Series.
        """
        feature_cols = [c for c in self.feature_cols if c in df.columns]
        X = df[feature_cols].copy()
        y = df[target_col].copy() if target_col in df.columns else pd.Series(dtype=float)
        return X, y

    def save(self, path: Path) -> None:
        """Serialise the entire pipeline (encoder + scaler + config) to disk."""
        save_pickle(self, path)
        logger.info("FeatureEngineeringPipeline saved: %s", path)

    @classmethod
    def load(cls, path: Path) -> "FeatureEngineeringPipeline":
        """Load a saved pipeline from disk."""
        pipeline = load_pickle(path)
        logger.info("FeatureEngineeringPipeline loaded: %s", path)
        return pipeline

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _get_lag_cols(self) -> list[str]:
        """Return lag column names based on configured lag sizes."""
        return [f"lag_{lag}" for lag in self.lag_sizes]

    def _get_rolling_cols(self) -> list[str]:
        """Return rolling column names based on configured windows."""
        return get_rolling_feature_cols(self.rolling_windows)

    def _get_numeric_scale_cols(self, df: pd.DataFrame) -> list[str]:
        """Identify numeric columns suitable for scaling."""
        exclude = {"sales", "store", "item", "store_enc", "item_enc",
                   "promotion", "holiday", "festival", "weekend"}
        return [
            c for c in df.select_dtypes(include="number").columns
            if c not in exclude
        ]

    def _build_feature_list(self, df: pd.DataFrame, target_col: str) -> list[str]:
        """
        Build the ordered list of feature columns (everything except the target
        and metadata columns).
        """
        exclude = {
            target_col, "date", "store_name", "item_name",
            "category", "supplier", "warehouse",
        }
        return [c for c in df.columns if c not in exclude and df[c].dtype != object]
