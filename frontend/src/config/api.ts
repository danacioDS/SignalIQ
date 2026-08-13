export const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:10000';

export const API_ENDPOINTS = {
  health: `${API_BASE}/health`,
  ticker: (ticker: string) => `${API_BASE}/api/ticker/${ticker}`,
  prices: `${API_BASE}/api/prices`,
  signals: `${API_BASE}/api/signals-intel`,
  signalsLive: `${API_BASE}/api/signals-live`,
  metrics: `${API_BASE}/api/metrics`,
};

export const DEFAULT_TICKERS = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO', 'NOK'];
