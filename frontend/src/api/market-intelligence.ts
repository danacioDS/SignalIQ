/**
 * Market Intelligence - API Client
 * Intenta backend, fallback a mocks
 */

import { TickerAnalysisResponse } from '../types/market-intelligence';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://signaliq-l8mi.onrender.com';

// ============================================================
// DATOS MOCK
// ============================================================

const createMockData = (ticker: string): TickerAnalysisResponse => {
  const baseData: TickerAnalysisResponse = {
    ticker: ticker,
    companyName: ticker === 'NVDA' ? 'NVIDIA Corporation' :
                  ticker === 'AAPL' ? 'Apple Inc.' :
                  ticker === 'MSFT' ? 'Microsoft Corporation' :
                  ticker === 'TSLA' ? 'Tesla Inc.' :
                  ticker === 'GOOGL' ? 'Alphabet Inc.' :
                  ticker === 'META' ? 'Meta Platforms' :
                  ticker === 'AMD' ? 'Advanced Micro Devices' :
                  ticker === 'AMZN' ? 'Amazon.com Inc.' :
                  ticker === 'JPM' ? 'JPMorgan Chase' :
                  ticker === 'KO' ? 'Coca-Cola Company' : ticker,
    sector: 'Technology',
    industry: 'Semiconductors',
    ndi: 0,
    statusLabel: 'NEUTRAL',
    statusColor: 'yellow' as const,
    updatedAt: new Date().toLocaleString('en-US', { 
      timeZone: 'America/New_York',
      hour12: false 
    }),
    quantitativeMetrics: {
      sentiment: 0,
      momentum: 0,
      divergence: 0,
      sourcesCount: 0,
    },
    narrativeBreakdown: {
      consensusPercentage: 50,
      consensusLabel: 'Moderado',
      intensityPercentage: 50,
      intensityLabel: 'Moderada',
      dispersionValue: 0.5,
      dispersionLabel: 'Media',
      mediaBias: {
        centerBizPercentage: 60,
        leftPercentage: 20,
        rightPercentage: 20,
      },
    },
    narrativeExhaustion: {
      level: 'BAJA',
      conditionsObserved: 0,
      totalConditions: 3,
      conditionsDetails: [],
      disclaimer: 'Feature en fase beta. Requiere validación adicional.',
      isBeta: true,
    },
    aiInterpretation: `Análisis para ${ticker}. El NDI actual sugiere un mercado en equilibrio.`,
    newsSummary: {
      items: [],
      positiveCount: 0,
      negativeCount: 0,
      averageSentiment: 0,
    },
    relativeContext: {
      sectorName: 'Technology',
      comparison: {
        tickerSentiment: 0,
        sectorSentiment: 0,
        sentimentDifference: 0,
        sentimentLabel: '🟢 en línea con el sector',
        tickerConsensus: 50,
        sectorConsensus: 50,
        consensusDifference: 0,
        consensusLabel: '🟢 en línea con el sector',
        tickerExhaustion: 'BAJA',
        sectorExhaustion: 'BAJA',
        exhaustionLabel: '🟢 en línea con el sector',
      },
      sectorRanking: [],
      insight: `${ticker} se encuentra en línea con el promedio del sector.`,
    },
  };

  const overrides: Record<string, Partial<TickerAnalysisResponse>> = {
    NVDA: {
      ndi: 2.707,
      statusLabel: 'EXTREME OVERHEATING',
      statusColor: 'red',
      quantitativeMetrics: { sentiment: 1.156, momentum: -1.551, divergence: 2.707, sourcesCount: 42 },
      narrativeBreakdown: {
        consensusPercentage: 74,
        consensusLabel: 'Alto',
        intensityPercentage: 52,
        intensityLabel: 'Moderada',
        dispersionValue: 0.22,
        dispersionLabel: 'Baja',
        mediaBias: { centerBizPercentage: 60, leftPercentage: 20, rightPercentage: 20 },
      },
      narrativeExhaustion: {
        level: 'ALTA',
        conditionsObserved: 3,
        totalConditions: 3,
        conditionsDetails: [
          { id: 'c1', description: 'Sentiment (+1.156) vs Momentum (-1.551) → Divergencia extrema', isMet: true },
          { id: 'c2', description: 'Dispersión narrativa (0.22) → Baja (Efecto Cámara de Eco)', isMet: true },
          { id: 'c3', description: 'Cobertura mediática (42 fuentes) → Duplica media de 14 días', isMet: true },
        ],
        disclaimer: 'Feature en fase beta. Requiere validación adicional.',
        isBeta: true,
      },
      aiInterpretation: 'El desajuste cuantitativo en NVDA refleja una asimetría crítica: la cobertura mediática se mantiene en niveles de euforia institucional, mientras que la acción del precio experimenta un agotamiento distributivo.',
      relativeContext: {
        sectorName: 'Technology',
        comparison: {
          tickerSentiment: 1.156,
          sectorSentiment: 0.45,
          sentimentDifference: 0.70,
          sentimentLabel: '🟢 más positivo',
          tickerConsensus: 74,
          sectorConsensus: 58,
          consensusDifference: 16,
          consensusLabel: '🟢 más consenso',
          tickerExhaustion: 'ALTA',
          sectorExhaustion: 'MEDIA',
          exhaustionLabel: '🟠 +1 nivel',
        },
        sectorRanking: [
          { rank: 1, ticker: 'NVDA', companyName: 'NVIDIA', ndi: 2.707, regimeLabel: 'SELL', regimeColor: 'red' },
          { rank: 2, ticker: 'AMD', companyName: 'AMD', ndi: 1.791, regimeLabel: 'REDUCE', regimeColor: 'orange' },
          { rank: 3, ticker: 'INTC', companyName: 'Intel', ndi: 0.950, regimeLabel: 'MONITOR', regimeColor: 'yellow' },
          { rank: 4, ticker: 'IBM', companyName: 'IBM', ndi: 0.450, regimeLabel: 'HOLD', regimeColor: 'green' },
          { rank: 5, ticker: 'ORCL', companyName: 'Oracle', ndi: -0.200, regimeLabel: 'BUY', regimeColor: 'green' },
        ],
        insight: 'NVDA muestra el NDI más alto del sector tecnológico, indicando la mayor divergencia entre narrativa y precio.',
      },
    },
    AAPL: {
      ndi: 0.522,
      statusLabel: 'NEUTRAL',
      statusColor: 'yellow',
      quantitativeMetrics: { sentiment: 0.321, momentum: -0.201, divergence: 0.522, sourcesCount: 28 },
      companyName: 'Apple Inc.',
    },
    MSFT: {
      ndi: 0.733,
      statusLabel: 'WATCHING',
      statusColor: 'orange',
      quantitativeMetrics: { sentiment: 0.511, momentum: -0.222, divergence: 0.733, sourcesCount: 31 },
      companyName: 'Microsoft Corporation',
    },
    TSLA: {
      ndi: 1.272,
      statusLabel: 'WATCHING',
      statusColor: 'orange',
      quantitativeMetrics: { sentiment: 0.247, momentum: -1.025, divergence: 1.272, sourcesCount: 35 },
      companyName: 'Tesla Inc.',
      sector: 'Automotive',
      industry: 'Automotive Manufacturing',
    },
    GOOGL: {
      ndi: 0.095,
      statusLabel: 'NEUTRAL',
      statusColor: 'yellow',
      quantitativeMetrics: { sentiment: 0.113, momentum: 0.018, divergence: 0.095, sourcesCount: 24 },
      companyName: 'Alphabet Inc.',
    },
    META: {
      ndi: 1.097,
      statusLabel: 'WATCHING',
      statusColor: 'orange',
      quantitativeMetrics: { sentiment: 0.412, momentum: -0.685, divergence: 1.097, sourcesCount: 29 },
      companyName: 'Meta Platforms',
    },
    AMD: {
      ndi: 1.791,
      statusLabel: 'OVERHEATING',
      statusColor: 'orange',
      quantitativeMetrics: { sentiment: 0.532, momentum: -1.259, divergence: 1.791, sourcesCount: 33 },
      companyName: 'Advanced Micro Devices',
    },
    AMZN: {
      ndi: -0.377,
      statusLabel: 'STABLE',
      statusColor: 'green',
      quantitativeMetrics: { sentiment: -1.552, momentum: -1.176, divergence: -0.377, sourcesCount: 26 },
      companyName: 'Amazon.com Inc.',
    },
    JPM: {
      ndi: -1.091,
      statusLabel: 'ALIGNED',
      statusColor: 'green',
      quantitativeMetrics: { sentiment: 0.794, momentum: 1.885, divergence: -1.091, sourcesCount: 19 },
      companyName: 'JPMorgan Chase',
      sector: 'Financial',
      industry: 'Banking',
    },
    KO: {
      ndi: 0.931,
      statusLabel: 'WATCHING',
      statusColor: 'orange',
      quantitativeMetrics: { sentiment: -0.583, momentum: -1.514, divergence: 0.931, sourcesCount: 16 },
      companyName: 'Coca-Cola Company',
      sector: 'Consumer',
      industry: 'Beverages',
    },
  };

  const override = overrides[ticker];
  if (override) {
    return { ...baseData, ...override };
  }

  return baseData;
};

// ============================================================
// FUNCIÓN PRINCIPAL - Intenta backend, fallback a mocks
// ============================================================

export const fetchTickerAnalysis = async (ticker: string): Promise<TickerAnalysisResponse> => {
  try {
    // Intentar llamar al backend
    const response = await fetch(`${API_BASE_URL}/api/ticker/analysis/${ticker}`, {
      headers: {
        'Accept': 'application/json',
      },
    });

    // Si la respuesta no es OK, usar mock
    if (!response.ok) {
      console.warn(`Backend responded with ${response.status}, using mock data for ${ticker}`);
      await new Promise((resolve) => setTimeout(resolve, 300));
      return createMockData(ticker);
    }

    // Intentar parsear JSON
    const text = await response.text();
    try {
      const data = JSON.parse(text);
      return data;
    } catch (parseError) {
      // Si no es JSON válido, usar mock
      console.warn('Backend response is not valid JSON, using mock data');
      return createMockData(ticker);
    }
  } catch (error) {
    // Si hay error de red, usar mock
    console.warn(`Network error fetching ${ticker}, using mock data:`, error);
    await new Promise((resolve) => setTimeout(resolve, 300));
    return createMockData(ticker);
  }
};

// ============================================================
// FUNCIONES ADICIONALES
// ============================================================

export const searchTickers = async (query: string): Promise<string[]> => {
  const allTickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'KO'];
  
  await new Promise((resolve) => setTimeout(resolve, 200));
  
  if (!query || query.length < 1) return [];
  
  const lowerQuery = query.toLowerCase();
  return allTickers.filter(t => t.toLowerCase().includes(lowerQuery));
};

export const getSectorRanking = async (sector: string): Promise<any[]> => {
  const mockRanking = [
    { rank: 1, ticker: 'NVDA', ndi: 2.707, regime: 'SELL' },
    { rank: 2, ticker: 'AMD', ndi: 1.791, regime: 'REDUCE' },
    { rank: 3, ticker: 'INTC', ndi: 0.950, regime: 'MONITOR' },
    { rank: 4, ticker: 'IBM', ndi: 0.450, regime: 'HOLD' },
    { rank: 5, ticker: 'ORCL', ndi: -0.200, regime: 'BUY' },
  ];
  
  await new Promise((resolve) => setTimeout(resolve, 300));
  return mockRanking;
};
