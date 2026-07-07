// ============================================================
// MARKET INTELLIGENCE - TYPES
// ============================================================

export interface MeasuredMetrics {
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
  status: 'BAJA' | 'MEDIA' | 'ALTA' | 'CRÍTICA';
  conditionsObservedCount: number;
  totalConditionsCount: number;
  conditionsDetails: ExhaustionCondition[];
}

export interface NewsItem {
  id: string;
  source: string;
  stars: number;
  headline: string;
  sentimentScore: number;
}

export interface NewsSummaryData {
  items: NewsItem[];
  positiveCount: number;
  negativeCount: number;
  averageSentiment: number;
}

export interface RelativeContextData {
  sectorName: string;
  comparison: {
    tickerSentiment: number;
    sectorSentiment: number;
    sentimentLabel: string;
    tickerConsensus: number;
    sectorConsensus: number;
    consensusLabel: string;
    tickerExhaustion: string;
    sectorExhaustion: string;
    exhaustionLabel: string;
  };
  rankingMagnificent7: {
    rank: number;
    ticker: string;
    ndi: number;
  }[];
  insight: string;
}

export interface TickerAnalysisResponse {
  ticker: string;
  ndi: number;
  statusLabel: string;
  updatedAt: string;
  confidenceScore: number;
  measuredMetrics: MeasuredMetrics;
  narrativeBreakdown: NarrativeBreakdownData;
  narrativeExhaustion: NarrativeExhaustionData;
  aiInterpretation: string;
  newsSummary: NewsSummaryData;
  relativeContext: RelativeContextData;
}
