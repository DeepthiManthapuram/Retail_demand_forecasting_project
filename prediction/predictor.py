"""
predictor.py
============
DemandPredictor — the main prediction engine called by the FastAPI endpoint.

Workflow
--------
1. Validate store / item / horizon inputs
2. Load historical sales series from the database or CSV
3. Load the feature engineering pipeline
4. Load the best saved model (or the requested model)
5. Build future feature rows for the forecast horizon
6. Generate point forecasts
7. Generate confidence intervals
8. Post-process (clip negatives, round to int, format dates)
9. Return a structured PredictionResult

The predictor caches loaded models in memory to avoid disk I/O on
every request (cache expires after MODEL_CACHE_TTL_SECONDS).
"""

import sys
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from feature_engineering.pipeline import FeatureEngineeringPipeline
from feature_engineering.time_features import add_time_features
from models.model_registry import find_best_model_path, load_model
from models.base_model import BaseForecaster
from prediction.post_processor import post_process
from prediction.confidence import bootstrap_intervals
from config.constants import FORECAST_HORIZONS, STORE_NAMES, ITEM_NAMES, MODEL_AUTO
from config.settings import get_settings
from config.logging_config import get_logger
from utils.data_loader import load_raw_dataset, normalise_dataset, load_series
from utils.helpers import generate_future_dates, date_to_str

logger   = get_logger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Prediction result container
# ---------------------------------------------------------------------------
@dataclass
class PredictionResult:
    """
    Structured output returned by DemandPredictor.predict().

    Attributes:
        store:          Store ID.
        store_name:     Store display name.
        item:           Item ID.
        item_name:      Item display name.
        model_used:     Name of the model that generated the forecast.
        horizon:        Forecast horizon in days.
        forecast_dates: List of date strings.
        predicted_sales: List of integer predicted sales values.
        lower_bound:    90 % prediction interval lower bound.
        upper_bound:    90 % prediction interval upper bound.
        avg_sales:      Average predicted daily sales.
        max_sales:      Maximum predicted daily sales.
        min_sales:      Minimum predicted daily sales.
        prediction_ms:  Prediction latency in milliseconds.
        generated_at:   UTC timestamp of the prediction.
    """
    store:          int
    store_name:     str
    item:           int
    item_name:      str
    model_used:     str
    horizon:        int
    forecast_dates: list[str]   = field(default_factory=list)
    predicted_sales: list[int]  = field(default_factory=list)
    lower_bound:    list[int]   = field(default_factory=list)
    upper_bound:    list[int]   = field(default_factory=list)
    avg_sales:      float = 0.0
    max_sales:      int   = 0
    min_sales:      int   = 0
    prediction_ms:  float = 0.0
    generated_at:   str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        """Serialise to plain dictionary."""
        return {
            "store":          self.store,
            "store_name":     self.store_name,
            "item":           self.item,
            "item_name":      self.item_name,
            "model_used":     self.model_used,
            "horizon":        self.horizon,
            "forecast_dates": self.forecast_dates,
            "predicted_sales": self.predicted_sales,
            "lower_bound":    self.lower_bound,
            "upper_bound":    self.upper_bound,
            "avg_sales":      round(self.avg_sales, 2),
            "max_sales":      self.max_sales,
            "min_sales":      self.min_sales,
            "prediction_ms":  round(self.prediction_ms, 2),
            "generated_at":   self.generated_at,
        }


# ---------------------------------------------------------------------------
# In-memory model cache
# ---------------------------------------------------------------------------
_MODEL_CACHE: dict[str, tuple[BaseForecaster, float]] = {}
_PIPELINE_CACHE: dict[str, tuple[FeatureEngineeringPipeline, float]] = {}


def _get_cached_model(cache_key: str, path: Path, model_name: str) -> BaseForecaster:
    """
    Return a cached model or load from disk and cache it.

    Args:
        cache_key:  Unique string key for this model.
        path:       Path to the .pkl file.
        model_name: Model type identifier.

    Returns:
        Loaded BaseForecaster instance.
    """
    ttl = settings.model_cache_ttl_seconds
    now = time.time()

    if cache_key in _MODEL_CACHE:
        model, cached_at = _MODEL_CACHE[cache_key]
        if now - cached_at < ttl:
            logger.debug("Model cache HIT: %s", cache_key)
            return model

    logger.info("Loading model from disk: %s", path)
    model = load_model(path, model_name)
    _MODEL_CACHE[cache_key] = (model, now)
    return model


def _get_cached_pipeline(key: str, path: Path) -> FeatureEngineeringPipeline:
    """
    Return a cached feature-engineering pipeline or load from disk.

    Args:
        key:  Cache key string.
        path: Path to the pipeline .pkl file.

    Returns:
        FeatureEngineeringPipeline instance.
    """
    ttl = settings.model_cache_ttl_seconds
    now = time.time()

    if key in _PIPELINE_CACHE:
        pipeline, cached_at = _PIPELINE_CACHE[key]
        if now - cached_at < ttl:
            return pipeline

    pipeline = FeatureEngineeringPipeline.load(path)
    _PIPELINE_CACHE[key] = (pipeline, now)
    return pipeline


# ---------------------------------------------------------------------------
# Main predictor class
# ---------------------------------------------------------------------------
class DemandPredictor:
    """
    End-to-end demand forecasting engine.

    Usage::

        predictor = DemandPredictor()
        result    = predictor.predict(store=1, item=5, horizon=30)
    """

    def __init__(self) -> None:
        """Initialise predictor (no state required — all state is in cache)."""
        # Load dataset once at startup
        self._df: Optional[pd.DataFrame] = None

    def _get_full_df(self) -> pd.DataFrame:
        """Lazy-load and normalise the full dataset (cached in instance)."""
        if self._df is None:
            raw         = load_raw_dataset()
            self._df    = normalise_dataset(raw)
        return self._df

    def predict(
        self,
        store:      int,
        item:       int,
        horizon:    int = 30,
        model_name: str = MODEL_AUTO,
    ) -> PredictionResult:
        """
        Generate a demand forecast for the given Store × Item.

        Args:
            store:      Store identifier (1-10).
            item:       Item identifier (1-50).
            horizon:    Number of future days to forecast.
            model_name: Model to use.  'auto' selects the best saved model.

        Returns:
            PredictionResult with dates, forecasts, and confidence intervals.

        Raises:
            ValueError:       if store/item/horizon are invalid.
            FileNotFoundError: if no saved model is found.
        """
        t_start = time.perf_counter()

        # ---- Validate inputs ----
        self._validate_inputs(store, item, horizon)

        # ---- Load historical series ----
        full_df    = self._get_full_df()
        series_df  = load_series(store, item, df=full_df)
        last_date  = series_df["date"].max().date()

        # ---- Resolve model path — auto-train if no saved model exists ----
        model_path = find_best_model_path(store, item, model_name)

        if model_path is None:
            logger.info(
                "No saved model for store=%d item=%d model=%s — auto-training on-demand ...",
                store, item, model_name,
            )
            model, pipeline, resolved_model_name = self._auto_train_and_cache(
                store, item, series_df, model_name
            )
        else:
            resolved_model_name = model_path.stem.split("_")[0]

            # Load model from cache or disk
            cache_key = f"{resolved_model_name}_s{store}_i{item}"
            model     = _get_cached_model(cache_key, model_path, resolved_model_name)

            pipeline_path = settings.saved_models_dir / f"pipeline_s{store}_i{item}.pkl"
            if pipeline_path.exists():
                pipeline = _get_cached_pipeline(f"pipeline_s{store}_i{item}", pipeline_path)
            else:
                pipeline = FeatureEngineeringPipeline()
                pipeline.fit_transform(series_df, drop_na=True)

        # ---- Build future feature rows ----
        future_df = self._build_future_features(series_df, last_date, horizon)

        # ---- Align future_df to model's training feature columns ----
        # Drop 'date' and any non-numeric/unknown columns before prediction
        predict_df = self._align_to_model_features(future_df, pipeline)

        # ---- Run prediction ----
        try:
            point_preds  = model.predict(predict_df)
            lower, upper = model.predict_interval(predict_df)
        except NotImplementedError:
            # LSTM/GRU use a different prediction interface
            featured = pipeline.fit_transform(series_df, drop_na=True)
            last_n   = featured.tail(60).select_dtypes(include="number").values
            point_preds = model.predict_from_seed(last_n, horizon)  # type: ignore
            margin      = point_preds * 0.15
            lower, upper = np.maximum(0, point_preds - margin), point_preds + margin

        # ---- Post-process ----
        preds_int = post_process(point_preds)
        lower_int = post_process(lower)
        upper_int = post_process(upper)

        # ---- Build dates ----
        future_dates = generate_future_dates(last_date, horizon)
        date_strs    = [date_to_str(d) for d in future_dates]

        prediction_ms = (time.perf_counter() - t_start) * 1000

        result = PredictionResult(
            store=store,
            store_name=STORE_NAMES[store - 1] if 1 <= store <= 10 else f"Store {store}",
            item=item,
            item_name=ITEM_NAMES[item - 1] if 1 <= item <= 50 else f"Item {item}",
            model_used=resolved_model_name,
            horizon=horizon,
            forecast_dates=date_strs,
            predicted_sales=preds_int.tolist(),
            lower_bound=lower_int.tolist(),
            upper_bound=upper_int.tolist(),
            avg_sales=float(np.mean(preds_int)),
            max_sales=int(np.max(preds_int)),
            min_sales=int(np.min(preds_int)),
            prediction_ms=prediction_ms,
        )

        logger.info(
            "Prediction complete — store=%d, item=%d, horizon=%d, model=%s, ms=%.1f",
            store, item, horizon, resolved_model_name, prediction_ms,
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _validate_inputs(self, store: int, item: int, horizon: int) -> None:
        """
        Raise ValueError if any input parameter is outside valid range.

        Args:
            store:   Store ID.
            item:    Item ID.
            horizon: Forecast horizon in days.
        """
        if not (1 <= store <= 10):
            raise ValueError(f"store must be between 1 and 10, got {store}.")
        if not (1 <= item <= 50):
            raise ValueError(f"item must be between 1 and 50, got {item}.")
        if horizon not in FORECAST_HORIZONS:
            # Accept any horizon in the valid range — not strictly the preset list
            if not (7 <= horizon <= 90):
                raise ValueError(
                    f"horizon must be between 7 and 90 days, got {horizon}."
                )

    def _align_to_model_features(
        self,
        future_df: pd.DataFrame,
        pipeline: "FeatureEngineeringPipeline",
    ) -> pd.DataFrame:
        """
        Return only the numeric feature columns the model was trained on.

        Drops 'date' and any non-numeric columns that would crash tree-based
        models (XGBoost, LightGBM, Random Forest).

        Args:
            future_df: Raw future feature DataFrame from _build_future_features.
            pipeline:  Fitted FeatureEngineeringPipeline (has .feature_cols).

        Returns:
            Aligned numeric-only DataFrame with exactly the training columns.
        """
        # Start from pipeline's trained feature column list
        trained_cols = getattr(pipeline, "feature_cols", [])

        if trained_cols:
            # Keep only columns the model saw during training
            available = [c for c in trained_cols if c in future_df.columns]
            missing   = [c for c in trained_cols if c not in future_df.columns]
            if missing:
                # Fill any missing columns with 0 (safe default)
                for col in missing:
                    future_df[col] = 0
            predict_df = future_df[trained_cols].copy()
        else:
            # Fallback: drop all non-numeric and known metadata columns
            drop_cols = {"date", "store_name", "item_name", "category", "supplier"}
            predict_df = future_df.drop(
                columns=[c for c in drop_cols if c in future_df.columns],
                errors="ignore",
            ).select_dtypes(include=["number"])

        return predict_df

    def _build_future_features(
        self,
        series_df: pd.DataFrame,
        last_date: date,
        horizon: int,
    ) -> pd.DataFrame:
        """
        Construct a feature DataFrame for the future forecast horizon.

        For ML models, we need feature rows for each future day.
        Lag and rolling features are approximated using the last known values.

        Args:
            series_df: Historical series DataFrame.
            last_date: Last date in historical data.
            horizon:   Number of future days.

        Returns:
            DataFrame with one row per future day and all feature columns.
        """
        from datetime import timedelta

        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=horizon,
            freq="D",
        )

        future_df = pd.DataFrame({"date": future_dates})

        # Calendar features
        future_df = add_time_features(future_df)

        # Approximate lag features using last known values
        last_sales = series_df["sales"].iloc[-30:].values
        for lag in [1, 7, 14, 30]:
            if len(last_sales) >= lag:
                future_df[f"lag_{lag}"] = last_sales[-lag]
            else:
                future_df[f"lag_{lag}"] = last_sales[-1]

        # Rolling features from last known window
        for w in [7, 14, 30]:
            window_data = series_df["sales"].tail(w)
            future_df[f"rolling_mean_{w}"]   = float(window_data.mean())
            future_df[f"rolling_std_{w}"]    = float(window_data.std())
            future_df[f"rolling_median_{w}"] = float(window_data.median())
            future_df[f"rolling_max_{w}"]    = float(window_data.max())
            future_df[f"rolling_min_{w}"]    = float(window_data.min())

        future_df["expanding_mean"] = float(series_df["sales"].mean())

        # Store / item encoding
        future_df["store"]     = series_df["store"].iloc[0]
        future_df["item"]      = series_df["item"].iloc[0]
        future_df["store_enc"] = series_df["store"].iloc[0] - 1
        future_df["item_enc"]  = series_df["item"].iloc[0] - 1

        # External features (assume last known values carry forward)
        for col in ["promotion", "holiday", "festival", "temperature", "rainfall", "discount"]:
            if col in series_df.columns:
                future_df[col] = float(series_df[col].iloc[-1])
            else:
                future_df[col] = 0

        return future_df

    def _auto_train_and_cache(
        self,
        store:     int,
        item:      int,
        series_df: pd.DataFrame,
        requested_model: str,
    ) -> tuple:
        """
        Train the requested model on-the-fly and cache it.

        Uses the actual requested model type where feasible:
        - ML models (xgboost, lightgbm, random_forest): train directly
        - DL models (lstm, gru): train with fast/small settings (10 epochs)
        - Statistical (arima, sarima, prophet, naive, moving_average): train directly
        - auto: uses xgboost

        Args:
            store:           Store code.
            item:            Item code.
            series_df:       Historical series DataFrame.
            requested_model: The model name the user asked for.

        Returns:
            Tuple (fitted_model, fitted_pipeline, resolved_model_name).
        """
        from training.splitter import ChronologicalSplitter
        from models.model_registry import create_model
        from utils.helpers import model_key, generate_version_tag

        # Map requested model to actual model name
        STAT_MODELS = ("arima", "sarima", "prophet", "naive", "moving_average")
        DL_MODELS   = ("lstm", "gru")
        ML_MODELS   = ("xgboost", "lightgbm", "random_forest")

        actual_model_name = requested_model if requested_model != MODEL_AUTO else "xgboost"

        # 1. Feature engineering
        pipeline = FeatureEngineeringPipeline()
        featured = pipeline.fit_transform(series_df, drop_na=True)

        if len(featured) < 30:
            logger.warning("Too few rows (%d) after FE — using moving_average.", len(featured))
            from models.naive import MovingAverageForecaster
            naive = MovingAverageForecaster(window=7)
            X_all, y_all = pipeline.get_feature_matrix(featured)
            naive.fit(X_all, y_all)
            return naive, pipeline, "moving_average"

        # ---- Statistical models — don't need feature matrix, use raw series ----
        if actual_model_name in STAT_MODELS:
            try:
                model = create_model(actual_model_name)
                # Statistical models fit on the raw sales series
                X_all, y_all = pipeline.get_feature_matrix(featured)
                model.fit(X_all, y_all)
                resolved = actual_model_name
            except Exception as e:
                logger.warning("Statistical model %s failed (%s) — falling back to xgboost.", actual_model_name, e)
                actual_model_name = "xgboost"
                # fall through to ML path below
            else:
                # Save & cache
                settings.saved_models_dir.mkdir(parents=True, exist_ok=True)
                version   = generate_version_tag()
                key       = model_key(actual_model_name, store, item)
                save_path = settings.saved_models_dir / f"{key}_{version}.pkl"
                model.save(save_path)
                pipeline_path = settings.saved_models_dir / f"pipeline_s{store}_i{item}.pkl"
                pipeline.save(pipeline_path)
                cache_key = f"{actual_model_name}_s{store}_i{item}"
                _MODEL_CACHE[cache_key]    = (model, time.time())
                _PIPELINE_CACHE[f"pipeline_s{store}_i{item}"] = (pipeline, time.time())
                logger.info("On-demand training complete (%s) — saved to %s", actual_model_name, save_path.name)
                return model, pipeline, actual_model_name

        # 2. Chronological train/test split for ML/DL models
        splitter   = ChronologicalSplitter(train_frac=0.85, val_frac=0.10, test_frac=0.05)
        data_split = splitter.split(featured)
        X_train, y_train = pipeline.get_feature_matrix(data_split.train)
        X_val,   y_val   = pipeline.get_feature_matrix(data_split.val)

        # 3. Instantiate and train model
        if actual_model_name == "xgboost":
            fast_params = {"n_estimators": 300, "learning_rate": 0.10,
                           "max_depth": 5, "subsample": 0.8,
                           "colsample_bytree": 0.8, "verbosity": 0}
            model = create_model(actual_model_name, params=fast_params)

        elif actual_model_name == "lightgbm":
            fast_params = {"n_estimators": 300, "learning_rate": 0.10,
                           "max_depth": 5, "num_leaves": 31,
                           "subsample": 0.8, "colsample_bytree": 0.8,
                           "verbosity": -1}
            model = create_model(actual_model_name, params=fast_params)

        elif actual_model_name == "random_forest":
            fast_params = {"n_estimators": 150, "max_depth": 10,
                           "n_jobs": -1, "random_state": 42}
            model = create_model(actual_model_name, params=fast_params)

        elif actual_model_name in DL_MODELS:
            # Use fast settings: small LSTM/GRU with few epochs
            try:
                fast_params = {"epochs": 10, "batch_size": 32, "units": 32,
                               "dropout": 0.1, "verbose": 0}
                model = create_model(actual_model_name, **fast_params)
            except Exception as e:
                logger.warning("DL model %s init failed (%s) — using xgboost.", actual_model_name, e)
                actual_model_name = "xgboost"
                fast_params = {"n_estimators": 300, "learning_rate": 0.10,
                               "max_depth": 5, "verbosity": 0}
                model = create_model(actual_model_name, params=fast_params)
        else:
            # Unknown model — default to xgboost
            logger.warning("Unknown model '%s' — defaulting to xgboost.", actual_model_name)
            actual_model_name = "xgboost"
            fast_params = {"n_estimators": 300, "learning_rate": 0.10,
                           "max_depth": 5, "verbosity": 0}
            model = create_model(actual_model_name, params=fast_params)

        try:
            model.fit(X_train, y_train, X_val, y_val)
        except TypeError:
            # Some models don't accept X_val/y_val
            model.fit(X_train, y_train)

        # 4. Save to disk so next request is instant
        settings.saved_models_dir.mkdir(parents=True, exist_ok=True)
        version   = generate_version_tag()
        key       = model_key(actual_model_name, store, item)
        save_path = settings.saved_models_dir / f"{key}_{version}.pkl"
        model.save(save_path)

        pipeline_path = settings.saved_models_dir / f"pipeline_s{store}_i{item}.pkl"
        pipeline.save(pipeline_path)

        # 5. Warm the cache
        cache_key = f"{actual_model_name}_s{store}_i{item}"
        _MODEL_CACHE[cache_key]    = (model, time.time())
        _PIPELINE_CACHE[f"pipeline_s{store}_i{item}"] = (pipeline, time.time())

        logger.info("On-demand training complete (%s) — saved to %s", actual_model_name, save_path.name)
        return model, pipeline, actual_model_name

