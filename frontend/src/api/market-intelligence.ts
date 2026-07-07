/**
 * Market Intelligence - API Client
 * Combina: backend para NDI + frontend para precios reales (yfinance)
 */

import { TickerAnalysisResponse } from '../types/market-intelligence';
import { getStockData, StockData } from '../services/yfinance-service';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://signaliq-l8mi.onrender.com';

// ============================================================
// DATOS DE RESPALDO PARA NDI (si el backend falla)
// ============================================================

const FALLBACK_NDI: Record<string, any> = {
  'NVDA': { ndi: 2.707, sentiment: 1.156, momentum: -1.551, regime: 'EXTREME OVERHEATING', color: 'red' },
  'AAPL': { ndi: 0.522, sentiment: 0.321, momentum: -0.201, regime: 'NEUTRAL', color: 'yellow' },
  'MSFT': { ndi: 0.733, sentiment: 0.511, momentum: -0.222, regime: 'WATCHING', color: 'orange' },
  'TSLA': { ndi: 1.272, sentiment: 0.247, momentum: -1.025, regime: 'WATCHING', color: 'orange' },
  'GOOGL': { ndi: 0.095, sentiment: 0.113, momentum: 0.018, regime: 'NEUTRAL', color: 'yellow' },
  'META': { ndi: -1.097, sentiment: -1.554, momentum: -0.457, regime: 'ALIGNED', color: 'green' },
  'AMD': { ndi: 1.791, sentiment: 0.532, momentum: -1.259, regime: 'OVERHEATING', color: 'orange' },
  'AMZN': { ndi: -0.377, sentiment: -1.552, momentum: -1.176, regime: 'STABLE', color: 'green' },
  'JPM': { ndi: -1.091, sentiment: 0.794, momentum: 1.885, regime: 'ALIGNED', color: 'green' },
  'KO': { ndi: 0.931, sentiment: -0.583, momentum: -1.514, regime: 'WATCHING', color: 'orange' },
};

function classifyRegime(ndi: number) {
  if (ndi > 2.0) return { regime: 'EXTREME OVERHEATING', color: 'red', label: 'SELL' };
  if (ndi > 1.5) return { regime: 'OVERHEATING', color: 'orange', label: 'REDUCE' };
  if (ndi > 0.5) return { regime: 'WATCHING', color: 'orange', label: 'MONITOR' };
  if (ndi > -0.5) return { regime: 'NEUTRAL', color: 'yellow', label: 'HOLD' };
  if (ndi > -1.5) return { regime: 'ALIGNED', color: 'green', label: 'BUY' };
  if (ndi > -2.0) return { regime: 'STRONG UNDERVALUED', color: 'green', label: 'STRONG BUY' };
  return { regime: 'CAPITULATION', color: 'blue', label: 'ACCUMULATE' };
}

// ============================================================
// FUNCIÓN PRINCIPAL - Precios reales + NDI
// ============================================================

export const fetchTickerAnalysis = async (ticker: string): Promise<TickerAnalysisResponse> => {
  try {
    // 1. Obtener precio REAL desde Yahoo Finance (frontend)
    const stockData = await getStockData(ticker);
    
    // 2. Intentar obtener NDI del backend
    let ndiData: any = null;
    let ndiSource = 'fallback';
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/ticker/analysis/${ticker}`);
      if (response.ok) {
        const data = await response.json();
        if (data && data.ndi !== undefined) {
          ndiData = data;
          ndiSource = 'backend';
        }
      }
    } catch (e) {
      console.warn('⚠️ Backend no disponible, usando NDI de respaldo');
    }
    
    // Si no hay datos del backend, usar fallback
    if (!ndiData) {
      ndiData = FALLBACK_NDI[ticker] || { ndi: 0, sentiment: 0, momentum: 0 };
    }
    
    // 3. Clasificar régimen
    const regime = classifyRegime(ndiData.ndi || 0);
    
    // 4. Construir respuesta combinada
    return {
      ticker: ticker,
      companyName: stockData.companyName,
      sector: stockData.sector || 'Unknown',
      industry: 'Unknown',
      ndi: ndiData.ndi || 0,
      statusLabel: ndiData.regime || regime.regime,
      statusColor: ndiData.color || regime.color,
      updatedAt: new Date().toLocaleString('es-ES', { 
        timeZone: 'America/New_York',
        hour12: false 
      }),
      price: stockData.price,
      quantitativeMetrics: {
        sentiment: ndiData.sentiment || 0,
        momentum: ndiData.momentum || 0,
        divergence: ndiData.ndi || 0,
        sourcesCount: 30
      },
      narrativeBreakdown: {
        consensusPercentage: 74,
        consensusLabel: 'Alto',
        intensityPercentage: 52,
        intensityLabel: 'Moderada',
        dispersionValue: 0.22,
        dispersionLabel: 'Baja',
        mediaBias: {
          centerBizPercentage: 60,
          leftPercentage: 20,
          rightPercentage: 20
        }
      },
      narrativeExhaustion: {
        level: 'BAJA',
        conditionsObserved: 0,
        totalConditions: 3,
        conditionsDetails: [],
        disclaimer: 'Feature en fase beta.',
        isBeta: true
      },
      aiInterpretation: `${ticker}: NDI ${(ndiData.ndi || 0).toFixed(3)} - ${regime.regime}. Precio real: $${stockData.price.toFixed(2)} (${stockData.change > 0 ? '+' : ''}${stockData.changePercent.toFixed(2)}%)`,
      newsSummary: {
        items: [],
        positiveCount: 0,
        negativeCount: 0,
        averageSentiment: 0
      },
      relativeContext: {
        sectorName: stockData.sector || 'Unknown',
        comparison: {
          tickerSentiment: ndiData.sentiment || 0,
          sectorSentiment: 0,
          sentimentDifference: 0,
          sentimentLabel: '🟢 en línea con el sector',
          tickerConsensus: 50,
          sectorConsensus: 50,
          consensusDifference: 0,
          consensusLabel: '🟢 en línea con el sector',
          tickerExhaustion: 'BAJA',
          sectorExhaustion: 'BAJA',
          exhaustionLabel: '🟢 en línea con el sector'
        },
        sectorRanking: [
          { rank: 1, ticker: ticker, companyName: stockData.companyName,
            ndi: ndiData.ndi || 0, regimeLabel: regime.label || 'HOLD', regimeColor: regime.color || 'yellow' }
        ],
        insight: `${ticker}: NDI ${(ndiData.ndi || 0).toFixed(3)} - ${regime.regime}. Precio: $${stockData.price.toFixed(2)}`
      }
    };
    
  } catch (error) {
    console.error('❌ Error en fetchTickerAnalysis:', error);
    throw error;
  }
};

// ============================================================
// FUNCIONES ADICIONALES
// ============================================================

export const searchTickers = async (query: string): Promise<string[]> => {
  const allTickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO'];
  if (!query || query.length < 1) return [];
  return allTickers.filter(t => t.toLowerCase().includes(query.toLowerCase()));
};

export const getSectorRanking = async (sector: string): Promise<any[]> => {
  const tickers = ['NVDA', 'AMD', 'INTC', 'IBM', 'ORCL'];
  const results = await Promise.all(
    tickers.map(async (ticker, index) => {
      try {
        const data = await fetchTickerAnalysis(ticker);
        return {
          rank: index + 1,
          ticker: ticker,
          companyName: data.companyName || ticker,
          ndi: data.ndi || 0,
          regimeLabel: data.statusLabel || 'NEUTRAL',
          regimeColor: data.statusColor || 'yellow',
        };
      } catch {
        return {
          rank: index + 1,
          ticker: ticker,
          companyName: ticker,
          ndi: 0,
          regimeLabel: 'NEUTRAL',
          regimeColor: 'yellow',
        };
      }
    })
  );
  return results.sort((a, b) => b.ndi - a.ndi);
};
