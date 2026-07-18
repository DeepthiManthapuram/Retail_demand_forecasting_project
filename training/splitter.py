"""
splitter.py
===========
Chronological train / validation / test split utilities.

NEVER shuffles the data — temporal order must be preserved for time-series
models to avoid look-ahead bias.

Provides:
    - ChronologicalSplitter : single fixed split by date or fraction
    - TimeSeriesCVSplitter  : expanding-window cross-validation
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.constants import TRAIN_FRAC, VAL_FRAC, TEST_FRAC
from config.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class DataSplit:
    """Container for a single train / val / test partition."""
    train: pd.DataFrame
    val:   pd.DataFrame
    test:  pd.DataFrame

    @property
    def train_dates(self) -> tuple[str, str]:
        """Return (first_date, last_date) of the training set."""
        return str(self.train["date"].min().date()), str(self.train["date"].max().date())

    @property
    def val_dates(self) -> tuple[str, str]:
        """Return (first_date, last_date) of the validation set."""
        return str(self.val["date"].min().date()), str(self.val["date"].max().date())

    @property
    def test_dates(self) -> tuple[str, str]:
        """Return (first_date, last_date) of the test set."""
        return str(self.test["date"].min().date()), str(self.test["date"].max().date())


class ChronologicalSplitter:
    """
    Splits a time-series DataFrame into train / val / test sets
    using chronological ordering (no shuffling).

    Args:
        train_frac: Fraction of data used for training.
        val_frac:   Fraction of data used for validation.
        test_frac:  Fraction of data used for testing.
                    train_frac + val_frac + test_frac should equal 1.0.
    """

    def __init__(
        self,
        train_frac: float = TRAIN_FRAC,
        val_frac:   float = VAL_FRAC,
        test_frac:  float = TEST_FRAC,
    ) -> None:
        """Validate and store split fractions."""
        total = train_frac + val_frac + test_frac
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Fractions must sum to 1.0, got {total:.4f}")

        self.train_frac = train_frac
        self.val_frac   = val_frac
        self.test_frac  = test_frac

    def split(
        self,
        df: pd.DataFrame,
        date_col: str = "date",
    ) -> DataSplit:
        """
        Split the DataFrame chronologically.

        Args:
            df:       Sorted time-series DataFrame.
            date_col: Name of the date column used for sorting.

        Returns:
            DataSplit with train, val, and test DataFrames.
        """
        # Ensure sorted — critical for chronological split
        df = df.sort_values(date_col).reset_index(drop=True)
        n  = len(df)

        train_end = int(n * self.train_frac)
        val_end   = int(n * (self.train_frac + self.val_frac))

        split = DataSplit(
            train=df.iloc[:train_end].copy(),
            val=  df.iloc[train_end:val_end].copy(),
            test= df.iloc[val_end:].copy(),
        )

        logger.info(
            "Split - Train: %d rows %s to %s | Val: %d rows %s to %s | Test: %d rows %s to %s",
            len(split.train), *split.train_dates,
            len(split.val),   *split.val_dates,
            len(split.test),  *split.test_dates,
        )
        return split

    def split_by_date(
        self,
        df: pd.DataFrame,
        val_start:  str,
        test_start: str,
        date_col:   str = "date",
    ) -> DataSplit:
        """
        Split the DataFrame using explicit cut-off dates.

        Args:
            df:         Sorted time-series DataFrame.
            val_start:  First date of the validation period (YYYY-MM-DD).
            test_start: First date of the test period (YYYY-MM-DD).
            date_col:   Name of the date column.

        Returns:
            DataSplit.
        """
        val_ts  = pd.Timestamp(val_start)
        test_ts = pd.Timestamp(test_start)

        df = df.sort_values(date_col).reset_index(drop=True)
        dates = pd.to_datetime(df[date_col])

        split = DataSplit(
            train=df[dates < val_ts].copy(),
            val=  df[(dates >= val_ts) & (dates < test_ts)].copy(),
            test= df[dates >= test_ts].copy(),
        )

        logger.info(
            "Date-split — Train: %d | Val: %d | Test: %d rows",
            len(split.train), len(split.val), len(split.test),
        )
        return split


class TimeSeriesCVSplitter:
    """
    Expanding-window cross-validation for time series.

    At each fold the training window expands by ``step_size`` rows while
    the validation window is fixed at ``horizon`` rows.

    Args:
        n_splits:  Number of CV folds.
        horizon:   Validation window size in rows.
        min_train: Minimum rows required in the training set.
    """

    def __init__(
        self,
        n_splits:  int = 5,
        horizon:   int = 30,
        min_train: int = 365,
    ) -> None:
        """Initialise CV splitter."""
        self.n_splits  = n_splits
        self.horizon   = horizon
        self.min_train = min_train

    def split(
        self,
        df: pd.DataFrame,
        date_col: str = "date",
    ) -> Iterator[tuple[pd.DataFrame, pd.DataFrame]]:
        """
        Yield (train_df, val_df) tuples for each CV fold.

        Args:
            df:       Sorted time-series DataFrame.
            date_col: Date column name.

        Yields:
            Tuples of (train_df, val_df).
        """
        df   = df.sort_values(date_col).reset_index(drop=True)
        n    = len(df)
        step = max(1, (n - self.min_train - self.horizon) // self.n_splits)

        for fold in range(self.n_splits):
            train_end = self.min_train + fold * step
            val_end   = train_end + self.horizon

            if val_end > n:
                break

            train_df = df.iloc[:train_end].copy()
            val_df   = df.iloc[train_end:val_end].copy()

            logger.debug(
                "CV fold %d/%d — train: %d rows, val: %d rows",
                fold + 1, self.n_splits, len(train_df), len(val_df),
            )
            yield train_df, val_df
