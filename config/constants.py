"""
constants.py
============
Project-wide constants for the Retail Demand Forecasting application.
All hard-coded values are centralised here so they can be changed in one place.
"""

# ---------------------------------------------------------------------------
# Dataset dimensions (mirrors Kaggle competition + synthetic extension)
# ---------------------------------------------------------------------------
NUM_STORES: int = 10
NUM_ITEMS: int = 50
TOTAL_SERIES: int = NUM_STORES * NUM_ITEMS          # 500 independent time series

# ---------------------------------------------------------------------------
# Forecast horizons (days)
# ---------------------------------------------------------------------------
FORECAST_HORIZONS: list[int] = [7, 14, 30, 60, 90]
DEFAULT_HORIZON: int = 30

# ---------------------------------------------------------------------------
# Supported model names
# ---------------------------------------------------------------------------
MODEL_NAIVE: str = "naive"
MODEL_MOVING_AVG: str = "moving_average"
MODEL_ARIMA: str = "arima"
MODEL_SARIMA: str = "sarima"
MODEL_PROPHET: str = "prophet"
MODEL_RANDOM_FOREST: str = "random_forest"
MODEL_XGBOOST: str = "xgboost"
MODEL_LIGHTGBM: str = "lightgbm"
MODEL_LSTM: str = "lstm"
MODEL_GRU: str = "gru"
MODEL_AUTO: str = "auto"          # picks the best saved model

ALL_MODELS: list[str] = [
    MODEL_NAIVE,
    MODEL_MOVING_AVG,
    MODEL_ARIMA,
    MODEL_SARIMA,
    MODEL_PROPHET,
    MODEL_RANDOM_FOREST,
    MODEL_XGBOOST,
    MODEL_LIGHTGBM,
    MODEL_LSTM,
    MODEL_GRU,
]

ML_MODELS: list[str] = [
    MODEL_RANDOM_FOREST,
    MODEL_XGBOOST,
    MODEL_LIGHTGBM,
]

DL_MODELS: list[str] = [
    MODEL_LSTM,
    MODEL_GRU,
]

# ---------------------------------------------------------------------------
# Evaluation metrics
# ---------------------------------------------------------------------------
METRIC_MAE: str = "mae"
METRIC_RMSE: str = "rmse"
METRIC_MAPE: str = "mape"
METRIC_R2: str = "r2"
PRIMARY_METRIC: str = METRIC_RMSE   # used to select the "best" model

# ---------------------------------------------------------------------------
# Lag / rolling window sizes
# ---------------------------------------------------------------------------
LAG_SIZES: list[int] = [1, 7, 14, 30]
ROLLING_WINDOWS: list[int] = [7, 14, 30]

# ---------------------------------------------------------------------------
# Deep Learning hyper-parameters (defaults)
# ---------------------------------------------------------------------------
LSTM_UNITS: int = 64
GRU_UNITS: int = 64
DL_LOOKBACK: int = 60          # number of past days fed as input sequence
DL_EPOCHS: int = 50
DL_BATCH_SIZE: int = 32
DL_DROPOUT: float = 0.2

# ---------------------------------------------------------------------------
# Train / validation / test chronological split fractions
# ---------------------------------------------------------------------------
TRAIN_FRAC: float = 0.70
VAL_FRAC: float = 0.15
TEST_FRAC: float = 0.15

# ---------------------------------------------------------------------------
# File & directory names
# ---------------------------------------------------------------------------
DATASET_TRAIN_FILE: str = "train.csv"
DATASET_TEST_FILE: str = "test.csv"
SYNTHETIC_TRAIN_FILE: str = "synthetic_train.csv"
SAVED_MODELS_DIR: str = "saved_models"
LOGS_DIR: str = "logs"
REPORTS_DIR: str = "reports"

# ---------------------------------------------------------------------------
# Date formats
# ---------------------------------------------------------------------------
DATE_FORMAT: str = "%Y-%m-%d"

# ---------------------------------------------------------------------------
# Season mapping  (Northern Hemisphere)
# ---------------------------------------------------------------------------
SEASON_MAP: dict[int, str] = {
    1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Autumn", 10: "Autumn", 11: "Autumn",
    12: "Winter",
}

# ---------------------------------------------------------------------------
# Store & item metadata (used when seeding the database)
# ---------------------------------------------------------------------------
STORE_NAMES: list[str] = [
    "Hyderabad Central", "Mumbai Metro", "Delhi North", "Bangalore South",
    "Chennai East", "Kolkata West", "Pune City", "Ahmedabad Hub",
    "Jaipur Royal", "Surat Diamond",
]

ITEM_NAMES: list[str] = [
    'Whole Milk',      'Butter',         'Cheddar Cheese',  'Yogurt',         'Cream',
    'Orange Juice',    'Apple Juice',    'Mango Juice',     'Cola 2L',        'Green Tea',
    'Potato Chips',   'Popcorn',       'Biscuits',       'Cookies',       'Crackers',
    'Rice 5kg',       'Wheat Flour',   'Sugar 1kg',      'Salt 500g',     'Cooking Oil',
    'Frozen Pizza',   'Frozen Peas',   'Ice Cream',      'Frozen Chicken','Frozen Fish',
    'Shampoo 200ml',  'Conditioner',   'Soap Bar',       'Toothpaste',    'Body Lotion',
    'Dishwash Liquid','Laundry Powder','Floor Cleaner',  'Toilet Paper',  'Paper Towels',
    'White Bread',    'Brown Bread',   'Croissant',      'Bagel',         'Sourdough',
    'Banana 1kg',     'Apple 1kg',     'Tomato 500g',    'Spinach',       'Carrot 500g',
    'Chicken Breast', 'Beef Mince',    'Pork Ribs',      'Lamb Chops',    'Tuna Can',
]

ITEM_CATEGORIES: list[str] = [
    "Dairy", "Beverages", "Snacks", "Staples", "Frozen",
    "Personal Care", "Household", "Bakery", "Produce", "Meat",
]
