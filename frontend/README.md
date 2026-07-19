# 📈 RetailIQ — AI-Powered Retail Demand Forecasting Platform

## 🚀 Project Overview

**RetailIQ** is a comprehensive, production-ready Machine Learning and Time-Series demand forecasting system designed to predict daily product sales for retail store networks. It features a high-performance **FastAPI (Python)** backend and an interactive **React + TypeScript + Vite** web dashboard. 

The platform allows store managers and inventory planners to forecast sales across 10 stores and 50 products, optimize stock replenishments, visualize demand patterns, and download publication-quality PDF business reports.

---

## 🎯 Objectives

*   **Accurate Demand Predictions**: Forecast daily sales up to 30 days out using traditional statistical, ensemble machine learning, and deep learning models.
*   **Inventory Optimization**: Automatically recommend safety stock buffers and reorder quantities to reduce stockouts and prevent capital tie-ups.
*   **Supply Chain Planning**: Highlight peak demand dates to coordinate logistics, warehouse scheduling, and warehouse capacity preemptively.
*   **Actionable Business Guidance**: Convert raw time-series forecasts into direct priority actions (High/Medium/Low priority) for pricing, marketing, and restocking.

---

## ✨ Features

*   **🤖 Multi-Model Forecast Engine**: Select from 10+ algorithms or let the system automatically choose the best model for a store-item combination:
    *   *Ensemble Machine Learning*: XGBoost, LightGBM, Random Forest
    *   *Deep Learning*: LSTM, GRU (TensorFlow-based)
    *   *Statistical*: ARIMA, SARIMA, Prophet, Moving Average, Naive
*   **📊 Dynamic Forecast Visualizations**: Render interactive charts with target predictions, upper/lower confidence bounds, and historical trends powered by Plotly.
*   **📈 Real-time Hybrid Dashboard**: Visualizes overall system KPI cards, model accuracy, and prediction distributions, merging browser `localStorage` predictions with backend log databases.
*   **📋 Actionable PDF Reports**: Download professional PDF reports (generated via ReportLab) containing:
    *   KPI metrics (Average, Peak, Trough Demand, Range, and Volatility)
    *   Inventory buffer calculations (10% or 15% safety stock recommendations)
    *   Warehouse logistics pre-stocking dates
    *   Dynamic priority action tables
*   **⚡ Resilient & Serverless Optimized**:
    *   *Lazy Dependency Imports*: Heavy packages (TensorFlow, Prophet) are only imported when requested, resulting in sub-second API startup times.
    *   *Robust ML Fallbacks*: Automatically falls back to native scikit-learn estimators if XGBoost or LightGBM isn't installed.
    *   *Fast Database Copier*: Ephemeral SQLite database file mounts to `/tmp/` instantly, skipping slow startup migrations and timeouts.

---

## 🛠️ Tech Stack

### Frontend
*   **Core**: React 19, TypeScript, Vite
*   **Styling**: Modern CSS System (curated dark/glassmorphic theme, responsive layouts)
*   **Charts**: Plotly.js (`react-plotly.js`), Lucide Icons
*   **State Management**: Zustand

### Backend
*   **Framework**: Python (3.11+), FastAPI, Uvicorn
*   **ORM / Database**: SQLAlchemy, SQLite (with on-demand ephemeral replication)
*   **Settings & Validation**: Pydantic v2, Pydantic Settings

### Machine Learning Stack
*   **Estimators**: Scikit-Learn, XGBoost, LightGBM, Statsmodels, Prophet, TensorFlow

### Reporting
*   **PDF Engine**: ReportLab

---

## 📂 Project Structure

```
Retail_demand_forecasting_project/
├── api/                   # Vercel Serverless Entrypoint and requirements
├── backend/               # FastAPI core application code
│   ├── routers/           # Endpoint controllers (forecast, reports, dashboard, etc.)
│   ├── schemas/           # Pydantic request/response validation schemas
│   └── main.py            # FastAPI main entrypoint and lifespans
├── config/                # Environment configuration and logging setup
├── database/              # SQLAlchemy connection pools, models, and seed files
├── datasets/              # Data files and generator scripts
├── feature_engineering/   # Feature pipeline (lags, rolling averages, calendar flags)
├── frontend/              # React+TS frontend application
│   ├── src/
│   │   ├── api/           # Axios client configuration with dev proxy
│   │   ├── components/    # Reusable UI components (Navbar, Cards)
│   │   └── pages/         # Dashboard, Forecast, and Home views
│   └── package.json       # Frontend scripts and dependencies
├── models/                # Time-series wrappers and model registry
├── prediction/            # Forecast processor, confidence boots, post-processing
├── package.json           # Root monorepo workspace manager
├── vercel.json            # Vercel CDN routing and proxy configuration
└── requirements.txt       # Backend dependencies list
```

---

## 📊 Dataset

The model fits on a structured daily retail sales dataset containing:
*   **Master keys**: `date`, `store` (1-10), `item` (1-50)
*   **Target variable**: `sales` (daily unit count)
*   **Exogenous variables**: `promotion` (promo flags), `holiday` (holidays), `festival` (festivals), `weekend`, `temperature`, `rainfall`, `price`, `discount`.

A lightweight 90-day subset (`datasets/synthetic_train.csv` ~4.8MB) is tracked in the repository to support on-demand training and fast backend testing, while keeping memory usage under control.

---

## ⚙️ Installation & Running Locally

### 1. Clone the repository
```bash
git clone https://github.com/DeepthiManthapuram/Retail_demand_forecasting_project.git
cd Retail_demand_forecasting_project
```

### 2. Run the Backend (FastAPI)
It is recommended to use a virtual environment:
```bash
# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt

# Start the local FastAPI server
uvicorn backend.main:app --port 8000 --reload
```
The API docs will be available at `http://localhost:8000/docs` and the health check at `http://localhost:8000/health`.

### 3. Run the Frontend (Vite)
Open a new terminal in the project root:
```bash
# Move into frontend directory
cd frontend

# Install node modules
npm install

# Start Vite dev server
npm run dev
```
Open `http://localhost:5173` in your browser. Vite is configured to proxy all API requests to the local backend on port 8000 automatically.

---

## 🌐 Deployment Configuration

The application is architected to run in a decoupled production environment:

### Backend (Railway)
*   **URL**: `https://retaildemandforecastingproject-production.up.railway.app`
*   Deployed with SQLite master database seeds, full ML stack support, and on-demand model fitting.

### Frontend (netlify)
*   **URL**: `https://retail-demand-frontend.netlify.app/`
*   Deployed as a lightweight static web app.

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://retaildemandforecastingproject-production.up.railway.app/api/$1"
    },
    {
      "source": "/auth/(.*)",
      "destination": "https://retaildemandforecastingproject-production.up.railway.app/auth/$1"
    },
    {
      "source": "/health",
      "destination": "https://retaildemandforecastingproject-production.up.railway.app/health"
    },
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

---

## 📡 API Endpoints

| Endpoint | Method | Input / Schema | Description |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | None | System status, DB integrity, and model checks |
| `/api/predict` | `POST` | `PredictRequest` | Generate multi-step forecast bounds & KPI statistics |
| `/api/dashboard` | `GET` | None | Overall forecasting counts, model distributions, and log list |
| `/api/reports/pdf/{id}` | `GET` | Forecast ID | Generates/downloads a formatted ReportLab PDF document |
| `/api/dataset-info` | `GET` | None | Size and record metadata of active training dataset |
| `/api/model-info` | `GET` | None | Details of currently available model artifacts on disk |

---

## 📈 Workflow

```
   [ Daily Store × Item Sales Data ]
                  │
                  ▼
         [ Data Loader & Cache ]
                  │
                  ▼
      [ Feature Engineering Pipeline ]
   (Lags, Rolling Means, Calendar Flags)
                  │
                  ▼
         [ ML Model Registry ]
     (Dynamic Fit / Warm Pickle Cache)
                  │
                  ▼
     [ Confidence Bounds Bootstrap ]
                  │
                  ▼
       [ Visual Plotly Charts ]
                  │
                  ▼
     [ Business Reports PDF Generator ]
```

---

## 👩‍💻 Author

**Deepthi Manthapuram**
*   GitHub: [@DeepthiManthapuram](https://github.com/DeepthiManthapuram/Retail_demand_forecasting_project.git)

---

## 📄 License

This project is developed for educational and professional demonstration purposes.
