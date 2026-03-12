// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

// WebSocket endpoints
export const WS_ENDPOINTS = {
  ALLOCATIONS: '/ws/allocations',
} as const;

// API endpoints
export const API_ENDPOINTS = {
  SIMULATE_FAILURE: '/simulate/grid-failure',
  INSIGHTS: '/insights',
} as const;

// Performance targets (from requirements)
export const PERFORMANCE_TARGETS = {
  ALLOCATION_LATENCY_MS: 10,
  WEBSOCKET_LATENCY_MS: 50,
  RAG_RESPONSE_TIME_MS: 2000,
  DASHBOARD_FPS: 60,
} as const;

// Dashboard configuration
export const DASHBOARD_CONFIG = {
  MAX_STREAM_ROWS: 50,
  UPDATE_INTERVAL_MS: 100,
  RECONNECT_DELAY_MS: 1000,
  MAX_RECONNECT_ATTEMPTS: 5,
} as const;

// Priority tier colors
export const PRIORITY_COLORS = {
  1: 'bg-red-500', // Hospital - highest priority
  2: 'bg-yellow-500', // Factory - medium priority
  3: 'bg-blue-500', // Residential - lowest priority
} as const;

// Source type colors
export const SOURCE_COLORS = {
  Grid: 'bg-slate-500',
  Solar: 'bg-yellow-400',
  Battery: 'bg-green-500',
  Diesel: 'bg-red-600',
} as const;

// Action status colors
export const ACTION_COLORS = {
  maintain: 'bg-success-500',
  reduce: 'bg-warning-500',
  cutoff: 'bg-danger-500',
} as const;