// types/index.ts  — shared TypeScript types for the entire frontend

/** Prediction request payload */
export interface PredictRequest {
  store:   number;
  item:    number;
  horizon: number;
  model:   string;
}

/** Full prediction response from the API */
export interface PredictResponse {
  store:            number;
  store_name:       string;
  item:             number;
  item_name:        string;
  model_used:       string;
  horizon:          number;
  forecast_dates:   string[];
  predicted_sales:  number[];
  lower_bound:      number[];
  upper_bound:      number[];
  avg_sales:        number;
  max_sales:        number;
  min_sales:        number;
  prediction_ms:    number;
  response_time_ms: number;
  generated_at:     string;
  forecast_id?:     number;
}

/** Dashboard KPI cards */
export interface DashboardData {
  kpi: {
    total_stores:          number;
    total_items:           number;
    total_series:          number;
    forecasts_today:       number;
    total_predictions:     number;
    saved_models:          number;
    available_model_types: string[];
    best_model:            string;
  };
  recent_predictions: Array<{
    store:      number;
    item:       number;
    model:      string;
    horizon:    number;
    status:     string;
    created_at: string;
  }>;
  store_forecast_counts: Array<{ store: number; name: string; forecasts: number }>;
  item_forecast_counts:  Array<{ item: number; name: string; forecasts: number }>;
}

/** Health check response */
export interface HealthResponse {
  status:  string;
  app:     string;
  version: string;
  checks:  Record<string, string>;
}

/** Forecast history item */
export interface ForecastHistoryItem {
  id:           number;
  store:        number;
  store_name:   string;
  item:         number;
  item_name:    string;
  model_used:   string;
  horizon:      number;
  created_at:   string;
  avg_forecast: number;
}

/** Training request */
export interface TrainRequest {
  store:  number;
  item:   number;
  models: string[];
}

/** Training response */
export interface TrainResponse {
  task_id:  string;
  status:   string;
  message:  string;
  store:    number;
  item:     number;
}
