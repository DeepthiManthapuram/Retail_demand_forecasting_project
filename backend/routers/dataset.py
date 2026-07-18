"""
dataset.py  (router)
=====================
POST /api/upload-dataset  — upload a new CSV dataset
GET  /api/dataset-info    — info about the current dataset
"""

import sys
import io
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))

from config.settings import get_settings
from config.logging_config import get_logger

logger   = get_logger("backend.routers.dataset")
router   = APIRouter()
settings = get_settings()

MAX_UPLOAD_MB = 200


@router.post("/upload-dataset", summary="Upload a new CSV sales dataset")
async def upload_dataset(file: UploadFile = File(...)):
    """
    Accept a CSV file upload and save it as the active training dataset.

    The file must contain at minimum: date, store, item, sales columns.
    Maximum file size: 200 MB.

    Args:
        file: Uploaded CSV file.

    Returns:
        Confirmation with row count and column names.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)

    if size_mb > MAX_UPLOAD_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum allowed: {MAX_UPLOAD_MB} MB.",
        )

    try:
        df = pd.read_csv(io.BytesIO(content), nrows=5)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Cannot parse CSV: {exc}")

    required = {"date", "store", "item", "sales"}
    missing  = required - set(df.columns.str.lower().tolist())
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"CSV is missing required columns: {missing}",
        )

    # Save to datasets/
    dest = settings.datasets_dir / "uploaded_train.csv"
    with open(dest, "wb") as fh:
        fh.write(content)

    # Count rows without loading full file
    full_df = pd.read_csv(io.BytesIO(content))
    logger.info("Dataset uploaded: %s (%d rows)", file.filename, len(full_df))

    return {
        "message":  "Dataset uploaded successfully.",
        "filename": file.filename,
        "rows":     len(full_df),
        "columns":  list(full_df.columns),
        "saved_as": str(dest),
    }


@router.get("/dataset-info", summary="Current dataset statistics")
def dataset_info():
    """
    Return metadata about the currently active dataset.

    Returns:
        Dictionary with file path, size, row count, and date range.
    """
    for candidate in ["uploaded_train.csv", "synthetic_train.csv", "train.csv"]:
        path = settings.datasets_dir / candidate
        if path.exists():
            try:
                df = pd.read_csv(path, nrows=3)
                df_full = pd.read_csv(path)
                dates = pd.to_datetime(df_full.get("date", pd.Series()))
                return {
                    "file":       candidate,
                    "path":       str(path),
                    "size_mb":    round(path.stat().st_size / (1024 * 1024), 2),
                    "rows":       len(df_full),
                    "columns":    list(df.columns),
                    "date_min":   str(dates.min().date()) if not dates.empty else "N/A",
                    "date_max":   str(dates.max().date()) if not dates.empty else "N/A",
                    "stores":     int(df_full["store"].nunique()) if "store" in df_full else 0,
                    "items":      int(df_full["item"].nunique()) if "item" in df_full else 0,
                }
            except Exception as exc:
                return {"file": candidate, "error": str(exc)}

    return {"message": "No dataset found. Run python datasets/generate_dataset.py"}
