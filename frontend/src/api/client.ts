// api/client.ts — Axios HTTP client for all backend API calls

import axios from 'axios';
import type {
  PredictRequest, PredictResponse, DashboardData,
  HealthResponse, ForecastHistoryItem, TrainRequest, TrainResponse,
} from '../types';

/** Base URL — relative path in production or custom VITE_API_URL */
const BASE_URL = import.meta.env.VITE_API_URL || '';

/** Axios instance with base URL and default headers */
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

/** Attach JWT token to every request if present in localStorage */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ---- Health ----

/** GET /health — system health check */
export const getHealth = (): Promise<HealthResponse> =>
  api.get<HealthResponse>('/health').then((r) => r.data);

// ---- Forecast ----

/** POST /api/predict — generate demand forecast */
export const predict = (req: PredictRequest): Promise<PredictResponse> =>
  api.post<PredictResponse>('/api/predict', req).then((r) => r.data);

/** GET /api/forecast-history — list past forecasts */
export const getForecastHistory = (
  store?: number,
  item?: number,
  limit = 50
): Promise<ForecastHistoryItem[]> =>
  api
    .get<ForecastHistoryItem[]>('/api/forecast-history', { params: { store, item, limit } })
    .then((r) => r.data);

// ---- Dashboard ----

/** GET /api/dashboard — KPI cards and summary */
export const getDashboard = (): Promise<DashboardData> =>
  api.get<DashboardData>('/api/dashboard').then((r) => r.data);

/** GET /api/metrics — model performance metrics */
export const getMetrics = () =>
  api.get('/api/metrics').then((r) => r.data);

// ---- Training ----

/** POST /api/train-model — trigger background training */
export const trainModel = (req: TrainRequest): Promise<TrainResponse> =>
  api.post<TrainResponse>('/api/train-model', req).then((r) => r.data);

/** GET /api/train-status/{task_id} — poll training status */
export const getTrainStatus = (taskId: string) =>
  api.get(`/api/train-status/${taskId}`).then((r) => r.data);

// ---- Dataset ----

/** GET /api/dataset-info — current dataset metadata */
export const getDatasetInfo = () =>
  api.get('/api/dataset-info').then((r) => r.data);

// ---- Models ----

/** GET /api/model-info — all saved model artefacts */
export const getModelInfo = () =>
  api.get('/api/model-info').then((r) => r.data);

// ---- Reports ----

/** Build download URL for CSV report */
export const csvUrl  = (id: number) => `${BASE_URL}/api/reports/csv/${id}`;
/** Build download URL for Excel report */
export const excelUrl = (id: number) => `${BASE_URL}/api/reports/excel/${id}`;
/** Build download URL for PDF report */
export const pdfUrl  = (id: number) => `${BASE_URL}/api/reports/pdf/${id}`;

// ---- Auth ----

/** POST /auth/login — get JWT token */
export const login = (username: string, password: string) =>
  api
    .post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    .then((r) => {
      localStorage.setItem('access_token', r.data.access_token);
      return r.data;
    });

/** POST /auth/register — create new account */
export const register = (data: { username: string; email: string; password: string }) =>
  api.post('/auth/register', data).then((r) => {
    localStorage.setItem('access_token', r.data.access_token);
    return r.data;
  });

/** Clear local auth state */
export const logout = () => localStorage.removeItem('access_token');

export default api;
