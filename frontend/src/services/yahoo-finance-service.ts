/**
 * Servicio para obtener datos de Yahoo Finance desde el frontend
 * Usa la API REST de Yahoo Finance directamente (sin librerías externas)
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
const FALLBACK_DATA: Record<string, StockData> = {
  'NVDA': { ticker: 'NVDA', price: 204.14, companyName: 'NVIDIA Corporation', sector: 'Technology', change: 0, changePercent: 0 },
  'AAPL': { ticker: 'AAPL', price: 313.26, companyName: 'Apple Inc.', sector: 'Technology', change: 0, changePercent: 0 },
  'MSFT': { ticker: 'MSFT', price: 383.05, companyName: 'Microsoft Corporation', sector: 'Technology', change: 0, changePercent: 0 },
  'TSLA': { ticker: 'TSLA', price: 393.87, companyName: 'Tesla Inc.', sector: 'Automotive', change: 0, changePercent: 0 },
  'GOOGL': { ticker: 'GOOGL', price: 361.64, companyName: 'Alphabet Inc.', sector: 'Technology', change: 0, changePercent: 0 },
  'META': { ticker: 'META', price: 603.07, companyName: 'Meta Platforms', sector: 'Technology', change: 0, changePercent: 0 },
  'AMD': { ticker: 'AMD', price: 517.49, companyName: 'Advanced Micro Devices', sector: 'Technology', change: 0, changePercent: 0 },
  'AMZN': { ticker: 'AMZN', price: 243.56, companyName: 'Amazon.com Inc.', sector: 'Consumer', change: 0, changePercent: 0 },
  'JPM': { ticker: 'JPM', price: 330.52, companyName: 'JPMorgan Chase', sector: 'Financial', change: 0, changePercent: 0 },
  'KO': { ticker: 'KO', price: 83.40, companyName: 'Coca-Cola Company', sector: 'Consumer', change: 0, changePercent: 0 },
};

/**
 * Obtiene datos de un ticker desde Yahoo Finance
 * Usa la API pública de Yahoo Finance (no requiere API key)
 */
export const getStockData = async (ticker: string): Promise<StockData> => {
  try {
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
    const fallback = FALLBACK_DATA[ticker];
    if (fallback) {
      return fallback;
    }
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
 * Obtiene datos de múltiples tickers desde Yahoo Finance
 */
export const getMultipleStockData = async (tickers: string[]): Promise<Record<string, StockData>> => {
  const results: Record<string, StockData> = {};
  
  const batchSize = 5;
  for (let i = 0; i < tickers.length; i += batchSize) {
    const batch = tickers.slice(i, i + batchSize);
    const promises = batch.map(async (ticker) => {
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
  }
  
  return results;
};

/**
 * Obtiene precio e historial de un ticker desde Yahoo Finance
 */
export const getPriceFromYahoo = async (ticker: string): Promise<PriceData | null> => {
  try {
    const stockData = await getStockData(ticker);
    if (!stockData || stockData.price === 0) {
      return null;
    }

    // Obtener historial (30 días)
    const url = `https://query1.finance.yahoo.com/v8/finance/chart/${ticker}?interval=1d&range=1mo`;
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
      }
    });
    
    let history: Array<{ date: string; close: number }> = [];
    if (response.ok) {
      const data = await response.json();
      if (data?.chart?.result?.[0]) {
        const result = data.chart.result[0];
        const timestamps = result.timestamp || [];
        const closePrices = result.indicators?.quote?.[0]?.close || [];
        history = timestamps.map((timestamp: number, index: number) => ({
          date: new Date(timestamp * 1000).toISOString().split('T')[0],
          close: closePrices[index] || 0,
        }));
      }
    }

    return {
      ticker: ticker,
      price: stockData.price,
      change: stockData.change,
      changePercent: stockData.changePercent,
      companyName: stockData.companyName,
      sector: stockData.sector,
      history: history,
    };
  } catch (error) {
    console.error(`Error fetching price from Yahoo for ${ticker}:`, error);
    return null;
  }
};

/**
 * Obtiene precios e historial de múltiples tickers desde Yahoo Finance
 */
export const getPricesFromYahoo = async (tickers: string[]): Promise<Record<string, PriceData>> => {
  const results: Record<string, PriceData> = {};
  
  const batchSize = 3;
  for (let i = 0; i < tickers.length; i += batchSize) {
    const batch = tickers.slice(i, i + batchSize);
    const promises = batch.map(ticker => getPriceFromYahoo(ticker));
    const batchResults = await Promise.all(promises);
    batchResults.forEach((result) => {
      if (result) {
        // ✅ Cambios aquí
        results[result.ticker] = {
          ticker: result.ticker,
          price: result.price,
          change: result.change,
          changePercent: result.changePercent,
          companyName: result.companyName || result.ticker,
          sector: result.sector || 'Unknown',
          history: result.history || [],
        };
      }
    });
  }
  
  return results;
};