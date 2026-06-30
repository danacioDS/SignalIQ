import { useMemo } from 'react';

interface SignalData {
  ticker: string;
  ndi: number;
  sentiment: number;
  momentum: number;
  price: number;
  sector: string;
  confidence: number;
}

interface RegimeAnalysis {
  regime: string;
  regimeKey: string;
  ndi: number;
  color: string;
  icon: string;
  explanation: {
    paragraph1: string;
    paragraph2: string;
    marketInsight: string;
    riskContext: string;
  };
}

const getRegimeFromNDI = (ndi: number): { key: string; label: string; color: string; icon: string } => {
  if (ndi > 2.0) return { key: 'EXTREME_OVERHEATING', label: 'Extreme Overheating', color: '#ef4444', icon: '🔴' };
  if (ndi > 1.5) return { key: 'OVERHEATING', label: 'Overheating', color: '#f97316', icon: '🟠' };
  if (ndi > 0.5) return { key: 'WATCHING', label: 'Watching', color: '#eab308', icon: '🟡' };
  if (ndi > -0.5) return { key: 'STABLE', label: 'Stable', color: '#22c55e', icon: '🟢' };
  if (ndi > -1.5) return { key: 'ALIGNED', label: 'Aligned', color: '#22c55e', icon: '🟢' };
  if (ndi > -2.0) return { key: 'STRONG_UNDERVALUED', label: 'Strong Undervalued', color: '#3b82f6', icon: '🔵' };
  return { key: 'EXTREME_UNDERVALUED', label: 'Extreme Undervalued', color: '#1d4ed8', icon: '🔵' };
};

export const useSignalAnalysis = (signal: SignalData | null | undefined): RegimeAnalysis => {
  return useMemo(() => {
    console.log('📊 useSignalAnalysis - input:', signal);

    if (!signal || typeof signal.ndi !== 'number' || isNaN(signal.ndi)) {
      return {
        regime: 'No Data',
        regimeKey: 'NO_DATA',
        ndi: 0,
        color: '#6b7280',
        icon: '⏳',
        explanation: {
          paragraph1: 'No market data available for this ticker.',
          paragraph2: 'Please check your connection or try again later.',
          marketInsight: 'Data not available',
          riskContext: 'Unknown risk level',
        },
      };
    }

    const ndi = signal.ndi;
    const sentiment = signal.sentiment ?? 0;
    const momentum = signal.momentum ?? 0;
    const price = signal.price ?? 0;
    const ticker = signal.ticker ?? 'Unknown';

    console.log(`📊 useSignalAnalysis - ${ticker}: ndi=${ndi}, sentiment=${sentiment}, momentum=${momentum}`);

    const regimeInfo = getRegimeFromNDI(ndi);
    
    let confidence = 0;
    const absNdi = Math.abs(ndi);
    if (absNdi <= 0.8) {
      confidence = 50 + (absNdi / 0.8) * 40;
    } else if (absNdi <= 2.0) {
      confidence = 90 - ((absNdi - 0.8) / 1.2) * 40;
    } else {
      confidence = 50;
    }
    confidence = Math.max(10, Math.min(95, confidence));

    let paragraph1 = '';
    let paragraph2 = '';
    let marketInsight = '';
    let riskContext = '';

    switch (regimeInfo.key) {
      case 'EXTREME_OVERHEATING':
        paragraph1 = `${ticker} is in an EXTREME OVERHEATING regime. Market sentiment has completely detached from price action, indicating a highly speculative environment.`;
        paragraph2 = `This configuration often precedes significant corrections. Consider reducing exposure or hedging positions.`;
        marketInsight = `NDI at ${ndi.toFixed(3)} reflects extreme divergence. Price: $${price.toFixed(2)}.`;
        riskContext = `High Risk - potential for sharp reversal. Confidence: ${confidence.toFixed(1)}%`;
        break;
      case 'OVERHEATING':
        paragraph1 = `${ticker} is in an OVERHEATING regime. Market sentiment is running ahead of price action, suggesting potential overvaluation.`;
        paragraph2 = `This type of configuration often appears during late-stage rallies. Price has not yet validated the optimism of sentiment.`;
        marketInsight = `NDI at ${ndi.toFixed(3)} reflects significant divergence. Price: $${price.toFixed(2)}.`;
        riskContext = `Medium-High Risk - caution advised. Confidence: ${confidence.toFixed(1)}%`;
        break;
      case 'WATCHING':
        paragraph1 = `${ticker} is in a WATCHING regime, indicating a moderate divergence between market sentiment and price momentum. This suggests the market is in a transitional phase.`;
        paragraph2 = `This type of configuration typically appears during market transition phases where price has not yet fully validated the optimism of sentiment. The divergence between sentiment (${sentiment.toFixed(3)}) and momentum (${momentum.toFixed(3)}) requires close monitoring.`;
        marketInsight = `NDI at ${ndi.toFixed(3)} reflects a structural divergence between sentiment and momentum. The market is in a phase of directional uncertainty.`;
        riskContext = `Medium Risk - this regime often precedes either continuation or reversal movements. Confidence: ${confidence.toFixed(1)}%`;
        break;
      case 'STABLE':
        paragraph1 = `${ticker} is in a STABLE regime. Market sentiment and price action are in equilibrium, suggesting a balanced market environment.`;
        paragraph2 = `This configuration typically appears during consolidation phases. Sentiment (${sentiment.toFixed(3)}) and momentum (${momentum.toFixed(3)}) are aligned.`;
        marketInsight = `NDI at ${ndi.toFixed(3)} reflects equilibrium. Price: $${price.toFixed(2)}.`;
        riskContext = `Low Risk - stable environment. Confidence: ${confidence.toFixed(1)}%`;
        break;
      case 'ALIGNED':
        paragraph1 = `${ticker} is in an ALIGNED regime. Price action is slightly outpacing sentiment, suggesting a potential accumulation opportunity.`;
        paragraph2 = `This configuration can indicate that the market is undervaluing the underlying fundamentals. Sentiment (${sentiment.toFixed(3)}) is lagging behind momentum (${momentum.toFixed(3)}).`;
        marketInsight = `NDI at ${ndi.toFixed(3)} reflects slight undervaluation. Price: $${price.toFixed(2)}.`;
        riskContext = `Low-Medium Risk - accumulation phase. Confidence: ${confidence.toFixed(1)}%`;
        break;
      case 'STRONG_UNDERVALUED':
        paragraph1 = `${ticker} is in a STRONG UNDERVALUED regime. Price action is significantly outpacing sentiment, suggesting a strong accumulation opportunity.`;
        paragraph2 = `This configuration often appears at market bottoms or after significant sell-offs. Sentiment (${sentiment.toFixed(3)}) is far behind momentum (${momentum.toFixed(3)}).`;
        marketInsight = `NDI at ${ndi.toFixed(3)} reflects strong undervaluation. Price: $${price.toFixed(2)}.`;
        riskContext = `Medium Risk - high reward potential. Confidence: ${confidence.toFixed(1)}%`;
        break;
      case 'EXTREME_UNDERVALUED':
        paragraph1 = `${ticker} is in an EXTREME UNDERVALUED regime. Market sentiment is extremely pessimistic while price action shows strength. This is a classic accumulation signal.`;
        paragraph2 = `This configuration is rare and often marks significant buying opportunities. The divergence between sentiment (${sentiment.toFixed(3)}) and momentum (${momentum.toFixed(3)}) is extreme.`;
        marketInsight = `NDI at ${ndi.toFixed(3)} reflects extreme undervaluation. Price: $${price.toFixed(2)}.`;
        riskContext = `High Risk - but highest potential reward. Confidence: ${confidence.toFixed(1)}%`;
        break;
      default:
        paragraph1 = `${ticker} is in a neutral regime. Market sentiment and price action are relatively aligned.`;
        paragraph2 = `No strong divergence detected. Sentiment (${sentiment.toFixed(3)}) and momentum (${momentum.toFixed(3)}) are in balance.`;
        marketInsight = `NDI at ${ndi.toFixed(3)}. Price: $${price.toFixed(2)}.`;
        riskContext = `Low Risk. Confidence: ${confidence.toFixed(1)}%`;
    }

    return {
      regime: regimeInfo.label,
      regimeKey: regimeInfo.key,
      ndi: ndi,
      color: regimeInfo.color,
      icon: regimeInfo.icon,
      explanation: {
        paragraph1,
        paragraph2,
        marketInsight,
        riskContext,
      },
    };
  }, [signal]);
};

export default useSignalAnalysis;
