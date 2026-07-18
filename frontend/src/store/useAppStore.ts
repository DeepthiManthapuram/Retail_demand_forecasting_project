// store/useAppStore.ts — Zustand global state management

import { create } from 'zustand';
import type { PredictResponse, DashboardData, HealthResponse } from '../types';

interface AppState {
  // System status
  health:         HealthResponse | null;
  systemReady:    boolean;
  setHealth:      (h: HealthResponse) => void;

  // Forecast
  forecastResult: PredictResponse | null;
  forecastLoading:boolean;
  forecastError:  string | null;
  setForecastResult:  (r: PredictResponse | null) => void;
  setForecastLoading: (v: boolean) => void;
  setForecastError:   (e: string | null) => void;

  // Dashboard
  dashboardData:    DashboardData | null;
  dashboardLoading: boolean;
  setDashboardData: (d: DashboardData) => void;
  setDashboardLoading: (v: boolean) => void;

  // Auth
  token:    string | null;
  username: string | null;
  role:     string | null;
  setAuth:  (token: string, username: string, role: string) => void;
  clearAuth:() => void;
}

export const useAppStore = create<AppState>((set) => ({
  // System
  health:      null,
  systemReady: false,
  setHealth: (h) => set({ health: h, systemReady: h.status === 'ok' }),

  // Forecast
  forecastResult:  null,
  forecastLoading: false,
  forecastError:   null,
  setForecastResult:  (r) => set({ forecastResult: r }),
  setForecastLoading: (v) => set({ forecastLoading: v }),
  setForecastError:   (e) => set({ forecastError: e }),

  // Dashboard
  dashboardData:    null,
  dashboardLoading: false,
  setDashboardData: (d) => set({ dashboardData: d }),
  setDashboardLoading: (v) => set({ dashboardLoading: v }),

  // Auth
  token:    localStorage.getItem('access_token'),
  username: localStorage.getItem('username'),
  role:     localStorage.getItem('role'),
  setAuth: (token, username, role) => {
    localStorage.setItem('access_token', token);
    localStorage.setItem('username', username);
    localStorage.setItem('role', role);
    set({ token, username, role });
  },
  clearAuth: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    localStorage.removeItem('role');
    set({ token: null, username: null, role: null });
  },
}));
