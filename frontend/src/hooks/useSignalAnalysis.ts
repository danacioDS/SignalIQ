import { useMemo } from 'react';
import { getRegimeFromNDI, getRegimeLabel, getRegimeColor, getRegimeIcon } from '../utils/velocimeterUtils';

interface SignalInput {
  ticker: string;
  ndi: number;
  sentiment: number;
  momentum: number;
  price: number;
  sector?: string;
  confidence?: number;
}

export const useSignalAnalysis = (input: SignalInput) => {
  return useMemo(() => {
    const regime = getRegimeFromNDI(input.ndi);
    const label = getRegimeLabel(regime);
    const color = getRegimeColor(regime);
    const icon = getRegimeIcon(regime);

    // Get regime-specific analysis
    const getRegimeAnalysis = (regime: string) => {
      const analyses: Record<string, { p1: string; p2: string; insight: string; risk: string }> = {
        'EXTREME_OVERHEATING': {
          p1: `${input.ticker} is in an EXTREME OVERHEATING regime, indicating extreme bullish sentiment disconnected from momentum. This represents a high-risk speculative phase where price has significantly outpaced fundamentals.`,
          p2: `Historical patterns suggest that extreme overheating regimes often precede sharp corrections. The divergence between sentiment (${input.sentiment.toFixed(3)}) and momentum (${input.momentum.toFixed(2)}%) is at critical levels.`,
          insight: `NDI at ${input.ndi.toFixed(3)} reflects extreme structural divergence. Market is in late-stage euphoria with elevated risk of reversal.`,
          risk: `Very High Risk - this regime typically precedes significant corrections or trend reversals.`,
        },
        'OVERHEATING': {
          p1: `${input.ticker} is in an OVERHEATING regime, suggesting strong bullish sentiment is outpacing momentum. This indicates the market may be overextended in the short term.`,
          p2: `This configuration often appears in late-stage rallies where price momentum is starting to slow. Sentiment (${input.sentiment.toFixed(3)}) remains elevated while momentum (${input.momentum.toFixed(2)}%) shows signs of weakening.`,
          insight: `NDI at ${input.ndi.toFixed(3)} indicates a structural divergence where sentiment is exceeding momentum. Watch for potential consolidation or reversal.`,
          risk: `High Risk - this regime often precedes pullbacks or trend exhaustion.`,
        },
        'WATCHING': {
          p1: `${input.ticker} is in a WATCHING regime, indicating a moderate divergence between market sentiment and price momentum. This suggests the market is in a transitional phase.`,
          p2: `This type of configuration typically appears during market transition phases where price has not yet fully validated the optimism of sentiment. The divergence between sentiment (${input.sentiment.toFixed(3)}) and momentum (${input.momentum.toFixed(2)}%) requires close monitoring.`,
          insight: `NDI at ${input.ndi.toFixed(3)} reflects a structural divergence between sentiment and momentum. The market is in a phase of directional uncertainty.`,
          risk: `Medium Risk - this regime often precedes either continuation or reversal movements.`,
        },
        'STABLE': {
          p1: `${input.ticker} is in a STABLE regime, indicating balanced conditions between sentiment and price momentum. This suggests the market is in equilibrium.`,
          p2: `This configuration typically appears when the market is consolidating. Sentiment (${input.sentiment.toFixed(3)}) and momentum (${input.momentum.toFixed(2)}%) are aligned, suggesting low volatility ahead.`,
          insight: `NDI at ${input.ndi.toFixed(3)} indicates balanced conditions. No immediate directional bias.`,
          risk: `Very Low Risk - this regime typically precedes low volatility periods.`,
        },
        'ALIGNED': {
          p1: `${input.ticker} is in an ALIGNED regime, indicating slightly negative sentiment is being offset by positive momentum. This often represents accumulation phases.`,
          p2: `This type of configuration suggests institutional accumulation may be occurring. Sentiment (${input.sentiment.toFixed(3)}) is slightly weak while momentum (${input.momentum.toFixed(2)}%) remains positive.`,
          insight: `NDI at ${input.ndi.toFixed(3)} suggests a divergence where momentum is stronger than sentiment.`,
          risk: `Low Risk - this regime typically precedes accumulation and trend formation.`,
        },
        'STRONG_UNDERVALUED': {
          p1: `${input.ticker} is in a STRONG UNDERVALUED regime, indicating negative sentiment is not justified by price momentum. This suggests potential oversold conditions.`,
          p2: `This configuration often appears during accumulation phases where sentiment (${input.sentiment.toFixed(3)}) is overly pessimistic while momentum (${input.momentum.toFixed(2)}%) remains resilient.`,
          insight: `NDI at ${input.ndi.toFixed(3)} indicates a structural divergence where momentum is stronger than sentiment.`,
          risk: `Medium-High Risk - this regime typically precedes reversals to the upside.`,
        },
        'EXTREME_UNDERVALUED': {
          p1: `${input.ticker} is in an EXTREME UNDERVALUED regime, indicating capitulation levels where sentiment is extremely negative while momentum shows signs of stabilization.`,
          p2: `This represents a phase of capitulation where price has become disconnected from sentiment. Sentiment (${input.sentiment.toFixed(3)}) is at extreme lows while momentum (${input.momentum.toFixed(2)}%) suggests potential stabilization.`,
          insight: `NDI at ${input.ndi.toFixed(3)} reflects extreme structural divergence - potential accumulation zone.`,
          risk: `High Risk - this regime typically precedes sharp reversals or trend changes.`,
        },
      };
      return analyses[regime] || analyses['STABLE'];
    };

    const analysis = getRegimeAnalysis(regime);

    return {
      ndi: input.ndi,
      regime,
      regimeLabel: label,
      regimeColor: color,
      regimeIcon: icon,
      decision: {
        action: 'MONITOR',
        priority: 'MEDIUM',
        risk: 'MEDIUM',
        confidence: input.confidence || 70,
      },
      explanation: {
        paragraph1: analysis.p1,
        paragraph2: analysis.p2,
        marketInsight: analysis.insight,
        riskContext: analysis.risk,
      },
      raw: input,
    };
  }, [input]);
};

export default useSignalAnalysis;
