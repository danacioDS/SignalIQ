/**
 * Market Intelligence - Tipos de datos
 * Contrato entre frontend y backend
 */

export interface QuantitativeMetrics {
  sentiment: number;
  momentum: number;
  divergence: number;
  sourcesCount: number;
}

export interface NarrativeBreakdownData {
  consensusPercentage: number;
  consensusLabel: string;
  intensityPercentage: number;
  intensityLabel: string;
  dispersionValue: number;
  dispersionLabel: string;
  mediaBias: {
    centerBizPercentage: number;
    leftPercentage: number;
    rightPercentage: number;
  };
}

export interface ExhaustionCondition {
  id: string;
  description: string;
  isMet: boolean;
}

export interface NarrativeExhaustionData {
  level: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRÍTICA';
  conditionsObserved: number;
  totalConditions: number;
  conditionsDetails: ExhaustionCondition[];
  disclaimer: string;
  isBeta: boolean;
}

export interface NewsItem {
  id: string;
  source: string;
  relevanceStars: number;
  headline: string;
  sentimentScore: number;
}

export interface NewsSummaryData {
  items: NewsItem[];
  positiveCount: number;
  negativeCount: number;
  averageSentiment: number;
}

export interface SectorRankingItem {
  rank: number;
  ticker: string;
  companyName: string;
  ndi: number;
  regimeLabel: string;
  regimeColor: string;
}

export interface RelativeContextData {
  sectorName: string;
  comparison: {
    tickerSentiment: number;
    sectorSentiment: number;
    sentimentDifference: number;
    sentimentLabel: string;
    tickerConsensus: number;
    sectorConsensus: number;
    consensusDifference: number;
    consensusLabel: string;
    tickerExhaustion: string;
    sectorExhaustion: string;
    exhaustionLabel: string;
  };
  sectorRanking: SectorRankingItem[];
  insight: string;
}

export interface TickerAnalysisResponse {
  ticker: string;
  companyName: string;
  sector: string;
  industry: string;
  ndi: number;
  statusLabel: string;
  statusColor: 'red' | 'orange' | 'yellow' | 'green' | 'blue';
  updatedAt: string;
  quantitativeMetrics: QuantitativeMetrics;
  narrativeBreakdown: NarrativeBreakdownData;
  narrativeExhaustion: NarrativeExhaustionData;
  aiInterpretation: string;
  newsSummary: NewsSummaryData;
  relativeContext: RelativeContextData;
}
