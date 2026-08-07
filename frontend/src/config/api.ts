/**
 * Centralized API configuration for SignalIQ frontend
 * All API URLs should be imported from this file
 */

// Get API base URL from environment or use default
export const API_BASE = process.env.REACT_APP_API_URL || 'https://signaliq-api.onrender.com';

// API endpoints
export const API_ENDPOINTS = {
    health: `${API_BASE}/health`,
    ticker: (ticker: string) => `${API_BASE}/api/ticker/${ticker}`,
    prices: `${API_BASE}/api/prices`,
    signals: `${API_BASE}/api/signals-intel`,
    signalsLive: `${API_BASE}/api/signals-live`,
    tickers: `${API_BASE}/api/tickers`,
};

// Default tracked tickers
export const DEFAULT_TICKERS = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO'];

// Export for convenience
export default {
    API_BASE,
    API_ENDPOINTS,
    DEFAULT_TICKERS,
};
