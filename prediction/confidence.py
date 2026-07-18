"""
confidence.py
=============
Bootstrap-based prediction interval generator for models that do not
natively provide uncertainty estimates (e.g. XGBoost, LightGBM).

The bootstrap method:
    1. Re-fit the model on N bootstrap samples of the training data.
    2. Generate predictions from each bootstrap model.
    3. Compute percentile-based confidence bounds.

This is computationally expensive for large series — use sparingly
(e.g. only for the Admin dashboard, not every API call).
"""

import numpy as np
import pandas as pd


def bootstrap_intervals(
    model,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_pred:  pd.DataFrame,
    n_bootstraps: int = 50,
    alpha: float = 0.10,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Estimate prediction intervals via bootstrap resampling.

    Args:
        model:        An unfitted BaseForecaster-compatible model instance.
                      Must implement fit() and predict().
        X_train:      Training features.
        y_train:      Training targets.
        X_pred:       Features for which to generate intervals.
        n_bootstraps: Number of bootstrap iterations.
        alpha:        Significance level (0.10 → 90 % interval).

    Returns:
        Tuple (lower_bound, upper_bound) as 1-D numpy arrays.
    """
    n    = len(X_train)
    preds = np.zeros((n_bootstraps, len(X_pred)))

    for b in range(n_bootstraps):
        # Sample with replacement
        idx       = np.random.randint(0, n, size=n)
        X_boot    = X_train.iloc[idx]
        y_boot    = y_train.iloc[idx]

        # Clone and fit
        import copy
        boot_model = copy.deepcopy(model)
        try:
            boot_model.fit(X_boot, y_boot)
            preds[b] = boot_model.predict(X_pred)
        except Exception:
            preds[b] = np.zeros(len(X_pred))

    lower_pct = (alpha / 2) * 100
    upper_pct = (1 - alpha / 2) * 100

    lower = np.maximum(0, np.percentile(preds, lower_pct, axis=0))
    upper = np.percentile(preds, upper_pct, axis=0)
    return lower, upper
