/**
 * Servicio para obtener datos de Yahoo Finance a través del proxy de Render
 * (Evita problemas de CORS)
 */

const API_BASE = 'https://signaliq-api.onrender.com';

export interface PriceData {
  ticker: string;
  price: number;
  change: number;
  changePercent: number;
  companyName: string;
  sector: string;
  history: Array<{ date: string; close: number }>;
}

/**
 * Obtiene precio e historial de un ticker desde Yahoo Finance (a través del proxy)
 */
export const getPriceFromYahoo = async (ticker: string): Promise<PriceData | null> => {
  try {
    const response = await fetch(`${API_BASE}/api/yahoo-price/${ticker}`, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    
    return {
      ticker: data.ticker,
      price: data.price || 0,
      change: data.change || 0,
      changePercent: data.changePercent || 0,
      companyName: data.companyName || ticker,
      sector: data.sector || 'Unknown',
      history: data.history || [],
    };
  } catch (error) {
    console.error(`Error fetching price for ${ticker}:`, error);
    return null;
  }
};

/**
 * Obtiene precios e historial de múltiples tickers desde Yahoo Finance
 */
export const getPricesFromYahoo = async (tickers: string[]): Promise<Record<string, PriceData>> => {
  const results: Record<string, PriceData> = {};
  
  const batchSize = 5;
  for (let i = 0; i < tickers.length; i += batchSize) {
    const batch = tickers.slice(i, i + batchSize);
    const promises = batch.map(ticker => getPriceFromYahoo(ticker));
    const batchResults = await Promise.all(promises);
    batchResults.forEach((result) => {
      if (result) {
        results[result.ticker] = result;
      }
    });
  }
  
  return results;
};