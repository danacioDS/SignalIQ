import { API_ENDPOINTS } from '../config/api';
/**
 * Servicio para obtener datos de Yahoo Finance desde el frontend
 * El navegador del usuario NO está bloqueado por Yahoo Finance
 */

export interface PriceData {
  ticker: string;
  price: number;
  change: number;
  changePercent: number;
  companyName: string;
  sector: string;
  history: Array<{ date: string; close: number }>;
}

// Datos de respaldo (fallback) en caso de error
const FALLBACK_DATA: Record<string, PriceData> = {
  'NVDA': { ticker: 'NVDA', price: 212.04, change: 0, changePercent: 0, companyName: 'NVIDIA Corporation', sector: 'Technology', history: [] },
  'AAPL': { ticker: 'AAPL', price: 187.45, change: 0, changePercent: 0, companyName: 'Apple Inc.', sector: 'Technology', history: [] },
  'MSFT': { ticker: 'MSFT', price: 425.30, change: 0, changePercent: 0, companyName: 'Microsoft Corporation', sector: 'Technology', history: [] },
  'TSLA': { ticker: 'TSLA', price: 410.18, change: 0, changePercent: 0, companyName: 'Tesla Inc.', sector: 'Automotive', history: [] },
  'GOOGL': { ticker: 'GOOGL', price: 365.84, change: 0, changePercent: 0, companyName: 'Alphabet Inc.', sector: 'Technology', history: [] },
  'META': { ticker: 'META', price: 574.14, change: 0, changePercent: 0, companyName: 'Meta Platforms', sector: 'Technology', history: [] },
  'AMD': { ticker: 'AMD', price: 157.32, change: 0, changePercent: 0, companyName: 'Advanced Micro Devices', sector: 'Technology', history: [] },
  'AMZN': { ticker: 'AMZN', price: 184.75, change: 0, changePercent: 0, companyName: 'Amazon.com Inc.', sector: 'Technology', history: [] },
  'JPM': { ticker: 'JPM', price: 335.83, change: 0, changePercent: 0, companyName: 'JPMorgan Chase', sector: 'Financial', history: [] },
  'KO': { ticker: 'KO', price: 62.45, change: 0, changePercent: 0, companyName: 'Coca-Cola Company', sector: 'Consumer', history: [] },
};

/**
 * Obtiene datos de un ticker desde Yahoo Finance
 * Usa la API pública de Yahoo Finance (no requiere API key)
 */
/*** */
export const getPriceFromYahoo = async (ticker: string): Promise<PriceData | null> => {
  try {
    const url = `${API_ENDPOINTS.prices}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Extraer el historial de precios
    const priceHistory = data.price_history || [];
    
    // Obtener el precio actual (el último elemento del historial)
    const lastPrice = priceHistory.length > 0 ? priceHistory[priceHistory.length - 1].close : 0;
    
    // Obtener el precio anterior para calcular el cambio
    const previousPrice = priceHistory.length > 1 ? priceHistory[priceHistory.length - 2].close : lastPrice;
    const change = lastPrice - previousPrice;
    const changePercent = previousPrice > 0 ? (change / previousPrice) * 100 : 0;
    
    return {
      ticker: ticker,
      price: lastPrice,
      change: change,
      changePercent: changePercent,
      companyName: ticker, // Podrías obtenerlo de otro endpoint
      sector: 'Unknown', // Podrías obtenerlo de otro endpoint
      history: priceHistory,
    };
    
  } catch (error) {
    console.warn(`⚠️ Error obteniendo datos de ${ticker}:`, error);
    console.info(`📊 Usando datos de respaldo para ${ticker}`);
    
    // Usar fallback
    const fallback = FALLBACK_DATA[ticker];
    if (fallback) {
      return fallback;
    }
    
    return null;
  }
};
/*** */
/**
 * Obtiene precios e historial de múltiples tickers desde Yahoo Finance
 */
export const getPricesFromYahoo = async (tickers: string[]): Promise<Record<string, PriceData>> => {
  const results: Record<string, PriceData> = {};
  
  // Procesar en paralelo (con límite de concurrencia)
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
