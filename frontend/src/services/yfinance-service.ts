/**
 * Servicio para obtener datos de Yahoo Finance desde el frontend
 * El navegador del usuario NO está bloqueado por Yahoo Finance
 */

export interface StockData {
  ticker: string;
  price: number;
  companyName: string;
  sector: string;
  change: number;
  changePercent: number;
}

// Datos de respaldo (fallback) en caso de error
const FALLBACK_DATA: Record<string, StockData> = {
  'NVDA': { ticker: 'NVDA', price: 212.04, companyName: 'NVIDIA Corporation', sector: 'Technology', change: 0, changePercent: 0 },
  'AAPL': { ticker: 'AAPL', price: 187.45, companyName: 'Apple Inc.', sector: 'Technology', change: 0, changePercent: 0 },
  'MSFT': { ticker: 'MSFT', price: 425.30, companyName: 'Microsoft Corporation', sector: 'Technology', change: 0, changePercent: 0 },
  'TSLA': { ticker: 'TSLA', price: 410.18, companyName: 'Tesla Inc.', sector: 'Automotive', change: 0, changePercent: 0 },
  'GOOGL': { ticker: 'GOOGL', price: 365.84, companyName: 'Alphabet Inc.', sector: 'Technology', change: 0, changePercent: 0 },
  'META': { ticker: 'META', price: 574.14, companyName: 'Meta Platforms', sector: 'Technology', change: 0, changePercent: 0 },
  'AMD': { ticker: 'AMD', price: 157.32, companyName: 'Advanced Micro Devices', sector: 'Technology', change: 0, changePercent: 0 },
  'AMZN': { ticker: 'AMZN', price: 184.75, companyName: 'Amazon.com Inc.', sector: 'Technology', change: 0, changePercent: 0 },
  'JPM': { ticker: 'JPM', price: 335.83, companyName: 'JPMorgan Chase', sector: 'Financial', change: 0, changePercent: 0 },
  'KO': { ticker: 'KO', price: 62.45, companyName: 'Coca-Cola Company', sector: 'Consumer', change: 0, changePercent: 0 },
};

/**
 * Obtiene datos de un ticker desde Yahoo Finance
 * Usa la API pública de Yahoo Finance (no requiere API key)
 */
export const getStockData = async (ticker: string): Promise<StockData> => {
  try {
    // Usar la API pública de Yahoo Finance
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}`;
    
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data.chart || !data.chart.result || data.chart.result.length === 0) {
      throw new Error('No se encontraron datos');
    }
    
    const result = data.chart.result[0];
    const meta = result.meta;
    const indicators = result.indicators.quote[0];
    
    // Obtener precio actual
    const price = meta.regularMarketPrice || meta.previousClose || 0;
    const previousClose = meta.previousClose || price;
    const change = price - previousClose;
    const changePercent = previousClose > 0 ? (change / previousClose) * 100 : 0;
    
    return {
      ticker: ticker,
      price: price,
      companyName: meta.longName || meta.shortName || ticker,
      sector: meta.sector || 'Unknown',
      change: change,
      changePercent: changePercent,
    };
    
  } catch (error) {
    console.warn(`⚠️ Error obteniendo datos de ${ticker}:`, error);
    console.info(`📊 Usando datos de respaldo para ${ticker}`);
    
    // Usar fallback
    const fallback = FALLBACK_DATA[ticker];
    if (fallback) {
      return fallback;
    }
    
    // Si no hay fallback, devolver datos básicos
    return {
      ticker: ticker,
      price: 0,
      companyName: ticker,
      sector: 'Unknown',
      change: 0,
      changePercent: 0,
    };
  }
};

/**
 * Obtiene datos de múltiples tickers
 */
export const getMultipleStockData = async (tickers: string[]): Promise<Record<string, StockData>> => {
  const results: Record<string, StockData> = {};
  
  // Procesar en paralelo
  const promises = tickers.map(async (ticker) => {
    try {
      const data = await getStockData(ticker);
      results[ticker] = data;
    } catch (error) {
      console.error(`❌ Error con ${ticker}:`, error);
      results[ticker] = FALLBACK_DATA[ticker] || {
        ticker: ticker,
        price: 0,
        companyName: ticker,
        sector: 'Unknown',
        change: 0,
        changePercent: 0,
      };
    }
  });
  
  await Promise.all(promises);
  return results;
};
