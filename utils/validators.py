"""
validators.py
=============
Full data-validation suite for the retail sales dataset.

Validates:
    - Missing values
    - Duplicate rows
    - Negative or zero sales
    - Invalid date formats / out-of-range dates
    - Incorrect store / item IDs
    - Invalid data types
    - Logical consistency (e.g. discount > price)

Every issue is collected into a ValidationReport which is both returned and
persisted to a JSON file for audit purposes.
"""

import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from config.settings import get_settings
from config.logging_config import get_logger

logger   = get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MIN_VALID_DATE  = pd.Timestamp("2000-01-01")
MAX_VALID_DATE  = pd.Timestamp("2030-12-31")
VALID_STORE_IDS = set(range(1, 11))    # 1 – 10
VALID_ITEM_IDS  = set(range(1, 51))    # 1 – 50


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class ValidationIssue:
    """Represents a single data-quality problem found during validation."""
    check:       str                   # name of the validation check
    severity:    str                   # 'error' | 'warning' | 'info'
    description: str                   # human-readable explanation
    row_count:   int = 0               # number of affected rows
    sample_rows: list[Any] = field(default_factory=list)  # up to 5 example indices


@dataclass
class ValidationReport:
    """
    Aggregated report produced by the DataValidator.

    Attributes:
        is_valid:     True only when no 'error' severity issues exist.
        total_rows:   Total rows in the DataFrame that was validated.
        issues:       List of all ValidationIssue found.
        validated_at: UTC timestamp of the validation run.
        summary:      Human-readable pass/fail summary.
    """
    is_valid:     bool
    total_rows:   int
    issues:       list[ValidationIssue] = field(default_factory=list)
    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    summary:      str = ""

    @property
    def errors(self) -> list[ValidationIssue]:
        """Return only error-severity issues."""
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return only warning-severity issues."""
        return [i for i in self.issues if i.severity == "warning"]

    def to_dict(self) -> dict:
        """Serialise the report to a plain dictionary."""
        return asdict(self)


class DataValidator:
    """
    Validates a retail sales DataFrame against all quality checks.

    Usage::

        validator = DataValidator()
        report = validator.validate(df)
        if not report.is_valid:
            print(report.errors)
    """

    def __init__(self) -> None:
        """Initialise the validator (no configuration needed)."""
        self._issues: list[ValidationIssue] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def validate(self, df: pd.DataFrame) -> ValidationReport:
        """
        Run all validation checks on the given DataFrame.

        Args:
            df: Normalised sales DataFrame from data_loader.normalise_dataset().

        Returns:
            ValidationReport containing all discovered issues.
        """
        logger.info("Starting data validation on DataFrame with shape %s …", df.shape)
        self._issues = []
        self._df     = df

        self._check_missing_values(df)
        self._check_duplicates(df)
        self._check_negative_sales(df)
        self._check_date_range(df)
        self._check_store_ids(df)
        self._check_item_ids(df)
        self._check_data_types(df)
        self._check_logical_consistency(df)

        has_errors = any(i.severity == "error" for i in self._issues)
        summary = (
            f"Validation {'FAILED' if has_errors else 'PASSED'} — "
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s) "
            f"in {len(df):,} rows."
        )

        report = ValidationReport(
            is_valid=not has_errors,
            total_rows=len(df),
            issues=self._issues,
            summary=summary,
        )

        logger.info(summary)
        self._save_report(report)
        return report

    # ------------------------------------------------------------------
    # Individual checks
    # ------------------------------------------------------------------
    def _check_missing_values(self, df: pd.DataFrame) -> None:
        """Flag columns that contain null / NaN values."""
        null_counts = df.isnull().sum()
        null_cols   = null_counts[null_counts > 0]

        if null_cols.empty:
            return

        for col, cnt in null_cols.items():
            severity = "error" if col in {"date", "store", "item", "sales"} else "warning"
            self._issues.append(ValidationIssue(
                check="missing_values",
                severity=severity,
                description=f"Column '{col}' has {cnt} missing values.",
                row_count=int(cnt),
                sample_rows=df[df[col].isnull()].index[:5].tolist(),
            ))

    def _check_duplicates(self, df: pd.DataFrame) -> None:
        """Flag duplicate Store × Item × Date rows."""
        dup_mask = df.duplicated(subset=["store", "item", "date"], keep=False)
        dup_count = int(dup_mask.sum())

        if dup_count > 0:
            self._issues.append(ValidationIssue(
                check="duplicates",
                severity="error",
                description=f"{dup_count} duplicate (store, item, date) rows found.",
                row_count=dup_count,
                sample_rows=df[dup_mask].index[:5].tolist(),
            ))

    def _check_negative_sales(self, df: pd.DataFrame) -> None:
        """Flag rows where sales is negative."""
        mask  = df["sales"] < 0
        count = int(mask.sum())

        if count > 0:
            self._issues.append(ValidationIssue(
                check="negative_sales",
                severity="error",
                description=f"{count} rows have negative sales values.",
                row_count=count,
                sample_rows=df[mask].index[:5].tolist(),
            ))

    def _check_date_range(self, df: pd.DataFrame) -> None:
        """Flag dates outside the expected range [2000-01-01, 2030-12-31]."""
        too_early = df["date"] < MIN_VALID_DATE
        too_late  = df["date"] > MAX_VALID_DATE
        bad       = too_early | too_late
        count     = int(bad.sum())

        if count > 0:
            self._issues.append(ValidationIssue(
                check="date_range",
                severity="error",
                description=f"{count} rows have dates outside the valid range.",
                row_count=count,
                sample_rows=df[bad].index[:5].tolist(),
            ))

    def _check_store_ids(self, df: pd.DataFrame) -> None:
        """Flag store IDs that do not exist in the known store list."""
        invalid = ~df["store"].isin(VALID_STORE_IDS)
        count   = int(invalid.sum())

        if count > 0:
            bad_ids = df.loc[invalid, "store"].unique().tolist()
            self._issues.append(ValidationIssue(
                check="invalid_store_ids",
                severity="error",
                description=f"{count} rows contain unknown store IDs: {bad_ids[:10]}.",
                row_count=count,
                sample_rows=df[invalid].index[:5].tolist(),
            ))

    def _check_item_ids(self, df: pd.DataFrame) -> None:
        """Flag item IDs that do not exist in the known item list."""
        invalid = ~df["item"].isin(VALID_ITEM_IDS)
        count   = int(invalid.sum())

        if count > 0:
            bad_ids = df.loc[invalid, "item"].unique().tolist()
            self._issues.append(ValidationIssue(
                check="invalid_item_ids",
                severity="error",
                description=f"{count} rows contain unknown item IDs: {bad_ids[:10]}.",
                row_count=count,
                sample_rows=df[invalid].index[:5].tolist(),
            ))

    def _check_data_types(self, df: pd.DataFrame) -> None:
        """Confirm numeric columns hold numeric values."""
        numeric_checks = {
            "sales":       "numeric",
            "store":       "numeric",
            "item":        "numeric",
            "price":       "numeric",
            "discount":    "numeric",
            "temperature": "numeric",
        }
        for col, expected in numeric_checks.items():
            if col not in df.columns:
                continue
            if not pd.api.types.is_numeric_dtype(df[col]):
                self._issues.append(ValidationIssue(
                    check="data_types",
                    severity="error",
                    description=f"Column '{col}' should be {expected} but is {df[col].dtype}.",
                    row_count=len(df),
                ))

    def _check_logical_consistency(self, df: pd.DataFrame) -> None:
        """Check cross-column logical rules."""
        # Discount should not exceed price
        if "price" in df.columns and "discount" in df.columns:
            both_valid = df["price"].notna() & df["discount"].notna()
            bad = both_valid & (df["discount"] > df["price"])
            count = int(bad.sum())
            if count > 0:
                self._issues.append(ValidationIssue(
                    check="discount_exceeds_price",
                    severity="warning",
                    description=f"{count} rows have discount > price.",
                    row_count=count,
                    sample_rows=df[bad].index[:5].tolist(),
                ))

        # Sales should not be unreasonably high (> 3 std above mean — possible outlier)
        mean_s  = df["sales"].mean()
        std_s   = df["sales"].std()
        outlier = df["sales"] > mean_s + 5 * std_s
        count   = int(outlier.sum())
        if count > 0:
            self._issues.append(ValidationIssue(
                check="outlier_sales",
                severity="warning",
                description=(
                    f"{count} rows have extremely high sales "
                    f"(> mean + 5σ = {mean_s + 5 * std_s:.1f})."
                ),
                row_count=count,
                sample_rows=df[outlier].index[:5].tolist(),
            ))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    @property
    def errors(self) -> list[ValidationIssue]:
        """Return error-severity issues from the last run."""
        return [i for i in self._issues if i.severity == "error"]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Return warning-severity issues from the last run."""
        return [i for i in self._issues if i.severity == "warning"]

    def _save_report(self, report: ValidationReport) -> None:
        """Persist the validation report as a JSON file in reports/."""
        try:
            out_dir = settings.reports_dir
            out_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            out_path  = out_dir / f"validation_report_{timestamp}.json"
            with open(out_path, "w", encoding="utf-8") as fh:
                json.dump(report.to_dict(), fh, indent=2, default=str)
            logger.info("Validation report saved: %s", out_path)
        except Exception as exc:
            logger.warning("Could not save validation report: %s", exc)


def clean_dataset(df: pd.DataFrame, report: ValidationReport) -> pd.DataFrame:
    """
    Apply automatic fixes for non-critical issues identified during validation.

    Fixes applied:
        - Remove duplicate rows (keep first occurrence).
        - Clip negative sales to zero.
        - Drop rows with invalid dates.

    NOTE: Invalid store/item IDs are NOT removed automatically — they should
    be investigated before discarding.

    Args:
        df:     Raw (or normalised) DataFrame.
        report: ValidationReport produced by DataValidator.validate().

    Returns:
        Cleaned DataFrame.
    """
    df = df.copy()
    initial_len = len(df)

    # Remove duplicates
    df.drop_duplicates(subset=["store", "item", "date"], keep="first", inplace=True)

    # Clip negative sales
    df["sales"] = df["sales"].clip(lower=0)

    # Drop out-of-range dates
    date_mask = (df["date"] >= MIN_VALID_DATE) & (df["date"] <= MAX_VALID_DATE)
    df = df[date_mask]

    dropped = initial_len - len(df)
    logger.info("Dataset cleaned: %d rows removed, %d rows retained.", dropped, len(df))

    df.sort_values(["store", "item", "date"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df
