"""
trainer.py
==========
ModelTrainer — orchestrates the full training pipeline for a single
Store × Item time series.

Pipeline
--------
1. Load series data
2. Apply feature engineering
3. Chronological split
4. Train each requested model
5. Evaluate on test set
6. Save model artefacts + metadata
7. Return evaluation report

Designed to be called per-series (one Store × Item at a time) or
for all 500 series in a loop from a higher-level script.
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from feature_engineering.pipeline import FeatureEngineeringPipeline
from training.splitter import ChronologicalSplitter, DataSplit
from models.model_registry import create_model, load_model
from evaluation.evaluator import ModelEvaluator
from evaluation.metrics import compute_all_metrics
from config.constants import ML_MODELS, MODEL_XGBOOST, MODEL_LIGHTGBM, MODEL_RANDOM_FOREST
from config.settings import get_settings
from config.logging_config import get_logger
from utils.helpers import model_key, generate_version_tag, save_json

logger   = get_logger(__name__)
settings = get_settings()


class ModelTrainer:
    """
    Orchestrates end-to-end training for one Store × Item combination.

    Attributes:
        store:       Store identifier.
        item:        Item identifier.
        models_to_train: List of model name strings to train.
        evaluator:   ModelEvaluator collecting all model results.

    Args:
        store:           Store code (int).
        item:            Item code (int).
        models_to_train: List of model names to train.
                         Defaults to ML_MODELS (RF, XGB, LGBM).
    """

    def __init__(
        self,
        store: int,
        item:  int,
        models_to_train: list[str] | None = None,
    ) -> None:
        """Initialise trainer for a specific Store × Item pair."""
        self.store           = store
        self.item            = item
        self.models_to_train = models_to_train or ML_MODELS
        self.evaluator       = ModelEvaluator()
        self._pipeline: Optional[FeatureEngineeringPipeline] = None
        self._split: Optional[DataSplit] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self, series_df: pd.DataFrame) -> dict:
        """
        Execute the full training pipeline for the given series.

        Args:
            series_df: DataFrame for one Store × Item, sorted by date.

        Returns:
            Dictionary with evaluation results, best model name, and file paths.
        """
        logger.info(
            "Training pipeline START — store=%d, item=%d, models=%s",
            self.store, self.item, self.models_to_train,
        )

        # ---- Step 1: Feature engineering ----
        self._pipeline = FeatureEngineeringPipeline()
        featured_df    = self._pipeline.fit_transform(series_df, drop_na=True)

        if len(featured_df) < 60:
            logger.warning(
                "Series s=%d i=%d has only %d rows after FE — skipping.",
                self.store, self.item, len(featured_df),
            )
            return {"status": "skipped", "reason": "insufficient_data"}

        # ---- Step 2: Chronological split ----
        splitter    = ChronologicalSplitter()
        self._split = splitter.split(featured_df)

        X_train, y_train = self._pipeline.get_feature_matrix(self._split.train)
        X_val,   y_val   = self._pipeline.get_feature_matrix(self._split.val)
        X_test,  y_test  = self._pipeline.get_feature_matrix(self._split.test)

        # ---- Step 3: Train and evaluate each model ----
        trained_paths: dict[str, str] = {}

        for model_name in self.models_to_train:
            try:
                self._train_one_model(
                    model_name=model_name,
                    X_train=X_train, y_train=y_train,
                    X_val=X_val,     y_val=y_val,
                    X_test=X_test,   y_test=y_test,
                    trained_paths=trained_paths,
                )
            except Exception as exc:
                logger.error(
                    "Failed training model=%s store=%d item=%d: %s",
                    model_name, self.store, self.item, exc, exc_info=True,
                )

        # ---- Step 4: Determine best model ----
        best_model_name = self.evaluator.best_model_name()
        report_path     = self.evaluator.save_report(
            filename=f"eval_s{self.store}_i{self.item}"
        )

        # ---- Step 5: Save feature pipeline alongside models ----
        pipeline_path = settings.saved_models_dir / f"pipeline_s{self.store}_i{self.item}.pkl"
        self._pipeline.save(pipeline_path)

        result = {
            "status":         "success",
            "store":          self.store,
            "item":           self.item,
            "best_model":     best_model_name,
            "trained_models": list(trained_paths.keys()),
            "model_paths":    trained_paths,
            "pipeline_path":  str(pipeline_path),
            "report_path":    str(report_path),
            "comparison":     self.evaluator.comparison_table().to_dict(orient="records"),
        }

        logger.info(
            "Training pipeline DONE — store=%d, item=%d, best=%s",
            self.store, self.item, best_model_name,
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _train_one_model(
        self,
        model_name: str,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_val:   pd.DataFrame,
        y_val:   pd.Series,
        X_test:  pd.DataFrame,
        y_test:  pd.Series,
        trained_paths: dict,
    ) -> None:
        """
        Train, evaluate, and save a single model.

        Args:
            model_name:    Model identifier string.
            X_train / y_train: Training features and target.
            X_val / y_val:     Validation features and target.
            X_test / y_test:   Test features and target.
            trained_paths: Mutable dict updated with the saved file path.
        """
        logger.info("  Training model: %s …", model_name)
        model = create_model(model_name)

        # ---- Fit ----
        t0 = time.perf_counter()
        if model_name in (MODEL_XGBOOST, MODEL_LIGHTGBM):
            model.fit(X_train, y_train, X_val, y_val)   # type: ignore
        else:
            model.fit(X_train, y_train)
        training_time = time.perf_counter() - t0

        # ---- Predict on test set ----
        t1 = time.perf_counter()
        y_pred = model.predict(X_test)
        pred_time = time.perf_counter() - t1

        # ---- Evaluate ----
        self.evaluator.add_result(
            model_name=model_name,
            y_true=y_test,
            y_pred=y_pred,
            training_time=training_time,
            prediction_time=pred_time,
        )

        # ---- Save ----
        version   = generate_version_tag()
        key       = model_key(model_name, self.store, self.item)
        save_path = settings.saved_models_dir / f"{key}_{version}.pkl"
        model.save(save_path)
        trained_paths[model_name] = str(save_path)

        logger.info(
            "    %s saved → %s (train=%.1fs)",
            model_name, save_path.name, training_time,
        )
