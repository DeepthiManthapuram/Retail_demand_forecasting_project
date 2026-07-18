# RetailIQ — Multi-Series Forecasting for Retail Demand Optimization

> **Production-Grade AI Demand Forecasting Platform**  
> Predict daily demand for every Store × Item combination using Machine Learning and Deep Learning.

---

## 🎯 Project Overview

RetailIQ is an end-to-end retail demand forecasting application that solves two costly business problems:

| Problem | Impact |
|---------|--------|
| **Stock Shortages** | Lost sales, dissatisfied customers |
| **Overstock** | Tied-up capital, storage costs, waste |

### What It Does

- Predicts **daily sales** for 500 Store × Item time series (10 stores × 50 products)
- Supports **7, 14, 30, 60, and 90-day** forecast horizons
- Trains **9 ML/DL models** per series and selects the best automatically
- Provides **90% prediction intervals** for risk-aware planning
- Delivers results via a **React dashboard** and a **REST API**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (Vite)                     │
│  Home · Forecast · Dashboard · History · Model Performance   │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / JSON
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                            │
│  /health · /api/predict · /api/train-model · /api/dashboard  │
│  /api/forecast-history · /api/reports/* · /auth/*            │
└────────┬──────────────────────────────┬────────────────────┘
         │                              │
┌────────▼────────┐          ┌──────────▼────────────────────┐
│  SQLite / PgSQL │          │      Prediction Engine         │
│  7 ORM Tables   │          │  DemandPredictor + Model Cache │
└─────────────────┘          └──────────┬────────────────────┘
                                        │
              ┌─────────────────────────▼────────────────────┐
              │           Feature Engineering Pipeline        │
              │  Time · Lag · Rolling · Encoding · Pipeline   │
              └─────────────────────────┬────────────────────┘
                                        │
              ┌─────────────────────────▼────────────────────┐
              │               9 Model Families                │
              │  Naive · MA · ARIMA/SARIMA · Prophet          │
              │  Random Forest · XGBoost · LightGBM           │
              │  LSTM · GRU                                    │
              └────────────────────────────────────────────────┘
```

---

## 🧠 ML Models

| Model | Type | Best For |
|-------|------|----------|
| Naïve | Baseline | Benchmark |
| Moving Average | Baseline | Smooth series |
| ARIMA | Statistical | Stationary series |
| SARIMA | Statistical | Strong weekly/yearly seasonality |
| Prophet | Statistical | Holiday effects, missing data |
| Random Forest | ML Ensemble | Feature-rich tabular data |
| **XGBoost** | **ML Ensemble** | **Kaggle-proven top performer** |
| **LightGBM** | **ML Ensemble** | **Fast, large-scale training** |
| LSTM | Deep Learning | Long-range temporal patterns |
| GRU | Deep Learning | Faster than LSTM, similar accuracy |

---

## 📁 Project Structure

```
Retail_demand_forecasting_project/
├── backend/                # FastAPI application
│   ├── main.py             # App factory + lifespan
│   ├── routers/            # health, forecast, training, dashboard, auth, reports
│   ├── schemas/            # Pydantic request/response models
│   └── services/           # Business logic service layer
├── config/                 # Settings, constants, logging
├── database/               # SQLAlchemy models, connection, seeder
├── datasets/               # Dataset generators and CSV files
├── evaluation/             # Metrics (RMSE, MAE, MAPE, etc.) + evaluator
├── feature_engineering/    # Time, lag, rolling, encoding pipeline
├── frontend/               # React 18 + TypeScript + Plotly SPA
│   └── src/
│       ├── pages/          # Home, Forecast, Dashboard, History, ModelPerformance, About, Login
│       ├── components/     # Navbar, Footer, charts
│       ├── api/            # Axios client
│       └── store/          # Zustand global state
├── models/                 # 9 forecaster classes + registry
├── prediction/             # DemandPredictor, post-processor, confidence intervals
├── training/               # Splitter, ModelTrainer
├── visualization/          # Server-side Plotly chart generators
├── tests/                  # pytest test suites
├── saved_models/           # Trained model .pkl files
├── logs/                   # Application log files
├── reports/                # Generated CSV/Excel/PDF reports
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## 🚀 Quick Start

### 1. Install Backend Dependencies

```bash
cd Retail_demand_forecasting_project
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your settings (SECRET_KEY, DATABASE_URL, etc.)
```

### 3. Generate Synthetic Dataset

```bash
python datasets/generate_dataset.py
```

### 4. Start the Backend

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## 🐳 Docker Deployment

```bash
# Copy and configure environment
copy .env.example .env

# Start all services (PostgreSQL + Backend + Frontend)
docker-compose up --build

# Access:
#   Frontend:  http://localhost:5173
#   API:       http://localhost:8000
#   API Docs:  http://localhost:8000/docs
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| POST | `/api/predict` | Generate demand forecast |
| GET | `/api/forecast-history` | Browse forecast records |
| POST | `/api/train-model` | Trigger model training (async) |
| GET | `/api/train-status/{task_id}` | Poll training status |
| GET | `/api/dashboard` | Dashboard KPIs + charts data |
| GET | `/api/dataset-info` | Current dataset metadata |
| POST | `/api/upload-dataset` | Upload a new CSV dataset |
| GET | `/api/model-info` | List saved model artefacts |
| GET | `/api/reports/csv/{id}` | Download forecast as CSV |
| GET | `/api/reports/excel/{id}` | Download forecast as Excel |
| GET | `/api/reports/pdf/{id}` | Download forecast as PDF |
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | JWT login |
| GET | `/auth/me` | Current user profile |

Full interactive docs: **http://localhost:8000/docs**

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📊 Dataset

The platform uses the **Demand Forecasting (Kernels Only)** dataset structure:

| Column | Type | Description |
|--------|------|-------------|
| date | DATE | Calendar date (daily) |
| store | INT | Store ID (1–10) |
| item | INT | Item ID (1–50) |
| sales | INT | Units sold that day |

Additional synthetic columns: `promotion`, `holiday`, `festival`, `temperature`, `rainfall`, `discount`.

---

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Language | Python 3.12+ | Core ML/API |
| API | FastAPI | High-performance REST |
| ML | XGBoost, LightGBM, Scikit-learn | Gradient boosting |
| DL | TensorFlow / Keras | LSTM & GRU |
| Time Series | Prophet, Statsmodels | ARIMA/SARIMA/Prophet |
| Database | SQLAlchemy + SQLite/PostgreSQL | ORM + persistence |
| Auth | python-jose + passlib | JWT + bcrypt |
| Frontend | React 18 + TypeScript | SPA UI |
| Charts | Plotly.js | Interactive visualisations |
| State | Zustand | Global state management |
| Build | Vite | Fast dev server |
| Containers | Docker + Compose | Deployment |

---

## 👤 Author

Built as a complete **production-quality** AI engineering project demonstrating:
- Clean Architecture (SOLID principles, PEP 8)
- Full-stack ML application development
- Enterprise API design patterns
- End-to-end MLOps workflow

---

*RetailIQ v1.0.0 · Multi-Series Retail Demand Forecasting Platform*