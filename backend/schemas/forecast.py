"""
forecast.py  (schemas)
=======================
Pydantic request and response models for the forecast endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    """Request body for POST /api/predict."""
    store:   int = Field(..., ge=1, le=10,  description="Store ID (1–10)")
    item:    int = Field(..., ge=1, le=50,  description="Item ID (1–50)")
    horizon: int = Field(30,  description="Forecast horizon in days", ge=7, le=90)
    model:   str = Field("auto", description="Model name or 'auto' for best model")

    class Config:
        json_schema_extra = {
            "example": {
                "store":   1,
                "item":    5,
                "horizon": 30,
                "model":   "auto",
            }
        }


class PredictResponse(BaseModel):
    """Response body for POST /api/predict."""
    store:           int
    store_name:      str
    item:            int
    item_name:       str
    model_used:      str
    horizon:         int
    forecast_dates:  list[str]
    predicted_sales: list[int]
    lower_bound:     list[int]
    upper_bound:     list[int]
    avg_sales:       float
    max_sales:       int
    min_sales:       int
    prediction_ms:   float
    response_time_ms: Optional[float] = None
    generated_at:    str
    forecast_id:     Optional[int] = None


class ForecastHistoryItem(BaseModel):
    """Single item in the forecast history list."""
    id:           int
    store:        int
    store_name:   str
    item:         int
    item_name:    str
    model_used:   str
    horizon:      int
    created_at:   str
    avg_forecast: float
