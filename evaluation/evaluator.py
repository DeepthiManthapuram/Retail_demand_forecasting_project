"""
evaluator.py
============
ModelEvaluator — runs every trained model against the test set and
produces a comparison table with all four metrics.

Also determines the "best" model based on the primary metric (RMSE).
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from evaluation.metrics import compute_all_metrics
from config.constants import PRIMARY_METRIC
from config.settings import get_settings
from config.logging_config import get_logger

logger   = get_logger(__name__)
settings = get_settings()


class ModelEvaluator:
    """
    Evaluates and compares multiple forecasting models.

    Usage::

        evaluator = ModelEvaluator()
        evaluator.add_result("xgboost",      y_true, y_pred_xgb, training_time=12.3)
        evaluator.add_result("lightgbm",     y_true, y_pred_lgb, training_time=9.1)
        evaluator.add_result("random_forest",y_true, y_pred_rf,  training_time=30.4)

        table      = evaluator.comparison_table()
        best_model = evaluator.best_model_name()
        evaluator.save_report()
    """

    def __init__(self) -> None:
        """Initialise an empty evaluator."""
        self._results: list[dict[str, Any]] = []

    def add_result(
        self,
        model_name: str,
        y_true: Any,
        y_pred: Any,
        training_time: float = 0.0,
        prediction_time: float = 0.0,
    ) -> None:
        """
        Evaluate a model and store its metrics.

        Args:
            model_name:      Identifier string for the model.
            y_true:          Ground-truth values (array-like).
            y_pred:          Predicted values (array-like).
            training_time:   Elapsed training time in seconds.
            prediction_time: Elapsed prediction time in seconds.
        """
        metrics = compute_all_metrics(y_true, y_pred)
        row = {
            "model":           model_name,
            "mae":             metrics["mae"],
            "rmse":            metrics["rmse"],
            "mape":            metrics["mape"],
            "r2":              metrics["r2"],
            "training_time_s": round(training_time, 2),
            "pred_time_ms":    round(prediction_time * 1000, 2),
        }
        self._results.append(row)
        logger.info(
            "Model %-20s | MAE=%.3f | RMSE=%.3f | MAPE=%.2f%% | R²=%.4f",
            model_name, metrics["mae"], metrics["rmse"], metrics["mape"], metrics["r2"],
        )

    def comparison_table(self) -> pd.DataFrame:
        """
        Build a sorted DataFrame comparing all added models.

        Returns:
            DataFrame sorted by PRIMARY_METRIC ascending (lower RMSE first).
        """
        if not self._results:
            return pd.DataFrame()
        df = pd.DataFrame(self._results)
        df.sort_values(PRIMARY_METRIC, ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def best_model_name(self) -> str:
        """
        Return the name of the model with the lowest PRIMARY_METRIC score.

        Returns:
            Model name string, or empty string if no results have been added.
        """
        if not self._results:
            return ""
        table = self.comparison_table()
        return str(table.iloc[0]["model"])

    def save_report(self, filename: str | None = None) -> Path:
        """
        Save the comparison table as both CSV and JSON to the reports directory.

        Args:
            filename: Optional base filename (without extension).
                      Auto-generated from timestamp if not provided.

        Returns:
            Path to the saved CSV report.
        """
        ts   = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        stem = filename or f"model_comparison_{ts}"

        out_dir = settings.reports_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        table    = self.comparison_table()
        csv_path = out_dir / f"{stem}.csv"
        json_path= out_dir / f"{stem}.json"

        table.to_csv(csv_path, index=False)
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(self._results, fh, indent=2, default=str)

        logger.info("Evaluation report saved: %s", csv_path)
        return csv_path
