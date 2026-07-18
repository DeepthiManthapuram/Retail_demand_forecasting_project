"""
plots.py
=========
Server-side plot generation using Plotly (for use in reports / notebooks).

Frontend uses react-plotly.js directly; this module is for:
  - Generating PNG/SVG images embedded in PDF reports
  - Jupyter notebook visualisations
  - CLI report generation scripts
"""

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from config.logging_config import get_logger

logger = get_logger(__name__)

# ---- Shared dark theme layout ----
DARK_LAYOUT = dict(
    paper_bgcolor = "rgba(5,13,26,1)",
    plot_bgcolor  = "rgba(10,22,40,1)",
    font          = dict(family="Inter, sans-serif", color="#94a3b8", size=12),
    legend        = dict(bgcolor="rgba(5,13,26,0.8)", bordercolor="rgba(96,165,250,0.2)", borderwidth=1),
)


def plot_forecast(
    forecast_dates:  list,
    predicted_sales: list,
    lower_bound:     Optional[list] = None,
    upper_bound:     Optional[list] = None,
    historical_dates: Optional[list] = None,
    historical_sales: Optional[list] = None,
    title: str = "Retail Demand Forecast",
) -> go.Figure:
    """
    Create an interactive Plotly figure showing the demand forecast
    with optional historical context and confidence intervals.

    Args:
        forecast_dates:   Date strings for the forecast period.
        predicted_sales:  Point forecast values.
        lower_bound:      90 % interval lower bound.
        upper_bound:      90 % interval upper bound.
        historical_dates: Historical date strings (optional).
        historical_sales: Historical sales values (optional).
        title:            Chart title.

    Returns:
        Plotly Figure object.
    """
    fig = go.Figure()

    # Historical
    if historical_dates and historical_sales:
        fig.add_trace(go.Scatter(
            x=historical_dates, y=historical_sales,
            name="Historical Sales",
            line=dict(color="#60a5fa", width=2),
            mode="lines",
        ))

    # Confidence interval
    if lower_bound and upper_bound:
        fig.add_trace(go.Scatter(
            x=list(forecast_dates) + list(reversed(forecast_dates)),
            y=list(upper_bound) + list(reversed(lower_bound)),
            fill="toself", fillcolor="rgba(139,92,246,0.12)",
            line=dict(color="transparent"),
            name="90% Confidence Interval",
            hoverinfo="skip",
        ))

    # Forecast line
    fig.add_trace(go.Scatter(
        x=forecast_dates, y=predicted_sales,
        name="Forecast",
        line=dict(color="#8b5cf6", width=2.5, dash="dot"),
        mode="lines+markers",
        marker=dict(size=5, color="#8b5cf6"),
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color="#e2e8f0", size=16)),
        xaxis=dict(title="Date", gridcolor="rgba(96,165,250,0.08)"),
        yaxis=dict(title="Daily Sales (units)", gridcolor="rgba(96,165,250,0.08)"),
        hovermode="x unified",
        **DARK_LAYOUT,
    )
    return fig


def plot_model_comparison(
    model_names: list[str],
    rmse_values: list[float],
    mae_values:  list[float],
) -> go.Figure:
    """
    Side-by-side bar chart comparing models by RMSE and MAE.

    Args:
        model_names: List of model name strings.
        rmse_values: RMSE per model.
        mae_values:  MAE per model.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure(data=[
        go.Bar(name="RMSE", x=model_names, y=rmse_values, marker_color="#3b82f6"),
        go.Bar(name="MAE",  x=model_names, y=mae_values,  marker_color="#8b5cf6"),
    ])
    fig.update_layout(
        barmode="group",
        title=dict(text="Model Comparison — RMSE & MAE", font=dict(color="#e2e8f0")),
        xaxis=dict(title="Model"),
        yaxis=dict(title="Error (units)"),
        **DARK_LAYOUT,
    )
    return fig


def plot_seasonality(df: pd.DataFrame, date_col: str = "date", sales_col: str = "sales") -> go.Figure:
    """
    Monthly and weekly seasonality patterns using box plots.

    Args:
        df:       DataFrame with date and sales columns.
        date_col: Name of the date column.
        sales_col:Name of the sales column.

    Returns:
        Plotly Figure with two subplots.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df["month"]  = df[date_col].dt.month_name()
    df["weekday"]= df[date_col].dt.day_name()

    fig = make_subplots(rows=1, cols=2, subplot_titles=["Monthly Seasonality", "Day-of-Week Pattern"])

    month_order   = ["January","February","March","April","May","June","July","August","September","October","November","December"]
    weekday_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    for m in month_order:
        vals = df.loc[df["month"] == m, sales_col].values
        if len(vals): fig.add_trace(go.Box(y=vals, name=m[:3], marker_color="#3b82f6"), row=1, col=1)

    for w in weekday_order:
        vals = df.loc[df["weekday"] == w, sales_col].values
        if len(vals): fig.add_trace(go.Box(y=vals, name=w[:3], marker_color="#8b5cf6"), row=1, col=2)

    fig.update_layout(showlegend=False, **DARK_LAYOUT)
    return fig


def plot_feature_importance(
    feature_names: list[str],
    importances:   list[float],
    top_n: int = 20,
) -> go.Figure:
    """
    Horizontal bar chart of feature importances.

    Args:
        feature_names: Feature name strings.
        importances:   Importance scores.
        top_n:         Number of top features to display.

    Returns:
        Plotly Figure.
    """
    df = pd.DataFrame({"feature": feature_names, "importance": importances})
    df = df.nlargest(top_n, "importance")

    fig = go.Figure(go.Bar(
        x=df["importance"], y=df["feature"],
        orientation="h",
        marker=dict(color=df["importance"], colorscale="Blues"),
    ))
    fig.update_layout(
        title=dict(text=f"Top {top_n} Feature Importances", font=dict(color="#e2e8f0")),
        xaxis=dict(title="Importance Score"),
        yaxis=dict(autorange="reversed"),
        **DARK_LAYOUT,
    )
    return fig


def save_figure(fig: go.Figure, path: Path, format: str = "html") -> None:
    """
    Save a Plotly figure to disk as HTML, PNG, or SVG.

    Args:
        fig:    Plotly Figure object.
        path:   Destination file path.
        format: 'html', 'png', or 'svg'.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if format == "html":
        fig.write_html(str(path))
    elif format in ("png", "svg", "pdf"):
        fig.write_image(str(path), format=format)
    logger.info("Figure saved: %s", path)
