"""
generate_dataset.py
===================
Synthetic retail demand dataset generator.

Produces a realistic dataset that mirrors the Kaggle "Demand Forecasting
(Kernels Only)" competition format **plus** the extended columns specified
in the project requirements:

    date, store, store_name, item, item_name, sales, promotion,
    holiday, temperature, rainfall, festival, weekend, inventory,
    price, discount, category, supplier, warehouse

The generator models realistic demand patterns including:
    - Long-term trend (slight upward)
    - Annual seasonality (Fourier terms)
    - Weekly seasonality (higher weekends)
    - Holiday / festival spikes
    - Promotion boosts
    - Store-level and item-level scale factors
    - Random noise

Usage (standalone):
    python datasets/generate_dataset.py

Output:
    datasets/synthetic_train.csv   — training data (2018-01-01 → 2023-12-31)
    datasets/synthetic_test.csv    — held-out test  (2024-01-01 → 2024-12-31)
"""

import os
import sys
import random
from pathlib import Path
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so config can be imported
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent          # datasets/
_ROOT = _HERE.parent                             # project root
sys.path.insert(0, str(_ROOT))

from config.constants import (
    NUM_STORES,
    NUM_ITEMS,
    STORE_NAMES,
    ITEM_CATEGORIES,
    DATE_FORMAT,
)

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED: int = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ---------------------------------------------------------------------------
# Date ranges
# ---------------------------------------------------------------------------
TRAIN_START = date(2018, 1, 1)
TRAIN_END   = date(2023, 12, 31)
TEST_START  = date(2024, 1, 1)
TEST_END    = date(2024, 12, 31)

# ---------------------------------------------------------------------------
# Metadata tables
# ---------------------------------------------------------------------------
ITEM_NAMES: list[str] = [
    "Whole Milk", "Butter", "Cheddar Cheese", "Yogurt", "Cream",
    "Orange Juice", "Apple Juice", "Mango Juice", "Cola 2L", "Green Tea",
    "Potato Chips", "Popcorn", "Biscuits", "Cookies", "Crackers",
    "Rice 5kg", "Wheat Flour", "Sugar 1kg", "Salt 500g", "Cooking Oil",
    "Frozen Pizza", "Frozen Peas", "Ice Cream Vanilla", "Frozen Chicken", "Frozen Fish",
    "Shampoo 200ml", "Conditioner 200ml", "Soap Bar", "Toothpaste", "Body Lotion",
    "Dishwasher Liquid", "Laundry Powder", "Floor Cleaner", "Toilet Paper", "Paper Towels",
    "White Bread", "Brown Bread", "Croissant", "Bagel", "Sourdough Loaf",
    "Banana 1kg", "Apple 1kg", "Tomato 500g", "Spinach Bunch", "Carrot 500g",
    "Chicken Breast", "Beef Mince", "Pork Ribs", "Lamb Chops", "Tuna Can",
]

SUPPLIERS: list[str] = [
    "FreshCo Distributors", "Metro Supply Chain", "AgriFirst Ltd",
    "GlobalFoods Inc", "QuickShip Logistics",
]

WAREHOUSES: list[str] = [
    "WH-North-1", "WH-South-2", "WH-East-3", "WH-West-4", "WH-Central-5",
]

# Indian public holidays (month, day)
HOLIDAYS: set[tuple[int, int]] = {
    (1, 26), (8, 15), (10, 2),          # Republic Day, Independence Day, Gandhi Jayanti
    (1, 1),  (12, 25),                  # New Year, Christmas
    (3, 29), (3, 30),                   # Holi (approx)
    (10, 15), (10, 16),                 # Dussehra (approx)
    (11, 5),  (11, 6),                  # Diwali (approx)
}

# Indian festivals that generate demand spikes
FESTIVALS: set[tuple[int, int]] = {
    (11, 5), (11, 6), (11, 7),   # Diwali
    (10, 14), (10, 15), (10, 16), # Navratri / Dussehra
    (3, 28), (3, 29),             # Holi
    (8, 14), (8, 15),             # Independence Day long weekend
    (12, 24), (12, 25), (12, 26), # Christmas week
    (1, 13), (1, 14),             # Pongal / Makar Sankranti
}


# ---------------------------------------------------------------------------
# Helper: sinusoidal annual seasonality
# ---------------------------------------------------------------------------
def _annual_seasonality(day_of_year: int, period: int = 365) -> float:
    """
    Return a seasonal component using the first two Fourier harmonics.

    Args:
        day_of_year: Integer day of year (1-365).
        period:      Annual period in days.

    Returns:
        Seasonal multiplier centred around 1.0 (range ≈ 0.85 – 1.15).
    """
    t = 2 * np.pi * day_of_year / period
    return 1.0 + 0.08 * np.sin(t) + 0.04 * np.cos(t) + 0.03 * np.sin(2 * t)


def _weekly_seasonality(day_of_week: int) -> float:
    """
    Return a weekly seasonality multiplier.

    Args:
        day_of_week: 0 = Monday … 6 = Sunday.

    Returns:
        Demand multiplier (weekends are higher).
    """
    # Mon-Thu: ~1.0, Fri: 1.10, Sat: 1.20, Sun: 1.15
    weekly = [1.00, 1.00, 1.00, 1.02, 1.10, 1.20, 1.15]
    return weekly[day_of_week]


# ---------------------------------------------------------------------------
# Core generator
# ---------------------------------------------------------------------------
def _generate_series(
    store_id: int,
    item_id: int,
    dates: list[date],
    store_scale: float,
    item_scale: float,
    base_sales: float,
) -> pd.DataFrame:
    """
    Generate a single Store × Item time series of daily sales.

    Args:
        store_id:     Integer store identifier (1-10).
        item_id:      Integer item identifier (1-50).
        dates:        List of date objects to generate rows for.
        store_scale:  Multiplicative scale factor for this store.
        item_scale:   Multiplicative scale factor for this item.
        base_sales:   Average baseline daily sales before any scaling.

    Returns:
        DataFrame with one row per date, containing all required columns.
    """
    rows = []
    n = len(dates)

    # Mild long-term trend: +5 % per year over the series
    trend_slope = 0.05 / 365.0

    for i, d in enumerate(dates):
        # ---- trend component ----
        trend = 1.0 + trend_slope * i

        # ---- seasonality ----
        annual_s  = _annual_seasonality(d.timetuple().tm_yday)
        weekly_s  = _weekly_seasonality(d.weekday())

        # ---- flags ----
        is_weekend  = int(d.weekday() >= 5)
        is_holiday  = int((d.month, d.day) in HOLIDAYS)
        is_festival = int((d.month, d.day) in FESTIVALS)

        # ---- promotion: ~15 % of days ----
        is_promo = int(random.random() < 0.15)

        # ---- demand multipliers ----
        holiday_mult  = 1.30 if is_holiday else 1.0
        festival_mult = 1.50 if is_festival else 1.0
        promo_mult    = 1.20 if is_promo else 1.0

        # ---- synthesize sales ----
        expected = (
            base_sales
            * store_scale
            * item_scale
            * trend
            * annual_s
            * weekly_s
            * holiday_mult
            * festival_mult
            * promo_mult
        )
        noise = np.random.normal(loc=0.0, scale=0.10 * expected)
        sales = max(0, round(expected + noise))

        # ---- weather simulation ----
        # Temperature: seasonal variation (India: 15-40°C)
        temp = 27.5 + 12.5 * np.sin(2 * np.pi * d.timetuple().tm_yday / 365 - np.pi / 2)
        temp += np.random.normal(0, 2.0)

        # Rainfall: higher Jun-Sep (monsoon)
        month = d.month
        rain_mean = 8.0 if 6 <= month <= 9 else 1.5
        rainfall = max(0.0, round(np.random.exponential(rain_mean), 1))

        # ---- inventory: simple reorder model ----
        inventory = max(0, int(expected * random.uniform(1.5, 3.0)))

        # ---- price & discount ----
        item_category = ITEM_CATEGORIES[(item_id - 1) % len(ITEM_CATEGORIES)]
        base_price = 50 + (item_id * 7) % 450          # 50 – 500 INR
        discount = round(random.choice([0, 5, 10, 15, 20]) if is_promo else 0, 1)
        price = round(base_price * (1 - discount / 100), 2)

        rows.append({
            "date":       d.strftime(DATE_FORMAT),
            "store":      store_id,
            "store_name": STORE_NAMES[store_id - 1],
            "item":       item_id,
            "item_name":  ITEM_NAMES[item_id - 1],
            "sales":      int(sales),
            "promotion":  is_promo,
            "holiday":    is_holiday,
            "temperature": round(temp, 1),
            "rainfall":   rainfall,
            "festival":   is_festival,
            "weekend":    is_weekend,
            "inventory":  inventory,
            "price":      price,
            "discount":   discount,
            "category":   item_category,
            "supplier":   SUPPLIERS[(store_id + item_id) % len(SUPPLIERS)],
            "warehouse":  WAREHOUSES[(store_id - 1) % len(WAREHOUSES)],
        })

    return pd.DataFrame(rows)


def generate_dataset(
    start: date,
    end: date,
    num_stores: int = NUM_STORES,
    num_items: int = NUM_ITEMS,
) -> pd.DataFrame:
    """
    Generate the full multi-series dataset for the given date range.

    Args:
        start:      First date of the dataset (inclusive).
        end:        Last date of the dataset (inclusive).
        num_stores: Number of stores to simulate.
        num_items:  Number of items to simulate.

    Returns:
        Sorted DataFrame with all Store × Item × Date rows.
    """
    dates = [start + timedelta(days=i) for i in range((end - start).days + 1)]

    # Unique scale factors so each store/item has its own demand level
    store_scales = {s: np.random.uniform(0.7, 1.5) for s in range(1, num_stores + 1)}
    item_scales  = {i: np.random.uniform(0.5, 2.0) for i in range(1, num_items + 1)}

    all_frames: list[pd.DataFrame] = []

    total = num_stores * num_items
    done  = 0

    for store_id in range(1, num_stores + 1):
        for item_id in range(1, num_items + 1):
            # Base daily sales: uniform 20-200 before scaling
            base = float(np.random.randint(20, 200))
            df = _generate_series(
                store_id=store_id,
                item_id=item_id,
                dates=dates,
                store_scale=store_scales[store_id],
                item_scale=item_scales[item_id],
                base_sales=base,
            )
            all_frames.append(df)
            done += 1
            if done % 50 == 0:
                print(f"  Generated {done}/{total} series …")

    combined = pd.concat(all_frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"])
    combined.sort_values(["store", "item", "date"], inplace=True)
    combined.reset_index(drop=True, inplace=True)

    return combined


def main() -> None:
    """
    Entry-point: generate training and test splits and save to CSV.
    Also prints basic statistics for a quick sanity check.
    """
    output_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Retail Demand Forecasting — Synthetic Dataset Generator")
    print("=" * 60)

    # ------------------------------------------------------------------
    # Training split  (2018-01-01 to 2023-12-31 → 6 years)
    # ------------------------------------------------------------------
    print("\n[1/2] Generating TRAINING dataset …")
    train_df = generate_dataset(TRAIN_START, TRAIN_END)
    train_path = output_dir / "synthetic_train.csv"
    train_df.to_csv(train_path, index=False)
    print(f"  Saved: {train_path}")
    print(f"  Rows : {len(train_df):,}")
    print(f"  Dates: {train_df['date'].min().date()} → {train_df['date'].max().date()}")
    print(f"  Stores: {train_df['store'].nunique()}  |  Items: {train_df['item'].nunique()}")

    # ------------------------------------------------------------------
    # Test split  (2024-01-01 to 2024-12-31 → 1 year held out)
    # ------------------------------------------------------------------
    print("\n[2/2] Generating TEST dataset …")
    test_df = generate_dataset(TEST_START, TEST_END)
    test_path = output_dir / "synthetic_test.csv"
    test_df.to_csv(test_path, index=False)
    print(f"  Saved: {test_path}")
    print(f"  Rows : {len(test_df):,}")

    # ------------------------------------------------------------------
    # Quick stats
    # ------------------------------------------------------------------
    print("\nSample statistics (training data):")
    print(train_df[["sales", "price", "temperature", "inventory"]].describe().round(2))
    print("\nDone! ✓")


if __name__ == "__main__":
    main()
