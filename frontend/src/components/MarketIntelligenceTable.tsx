import React from 'react';
import { getRegimeColor, getRegimeLabel, getRegimeIcon, REGIME_COLORS } from '../constants/colors';

interface TickerData {
  ticker: string;
  price: number;
  sentiment: number;
  momentum: number;
  ndi: number;
  regime: string;
  confidence: number;
}

interface MarketIntelligenceTableProps {
  tickers: TickerData[];
  onSelectTicker: (ticker: string) => void;
  selectedTicker: string | null;
}

export const MarketIntelligenceTable: React.FC<MarketIntelligenceTableProps> = ({
  tickers,
  onSelectTicker,
  selectedTicker,
}) => {

  const sortedTickers = [...tickers]
  .sort((a, b) => b.sentiment - a.sentiment)
  .slice(0, 5);

  const getBarWidth = (value: number, maxAbs: number = 0.3) => {
    const normalized = Math.min(Math.abs(value) / maxAbs, 1);
    return Math.max(normalized * 100, 5);
  };

  const getSentimentBarColor = (value: number) => {
    if (value > 0.05) return '#22c55e';
    if (value < -0.05) return '#ef4444';
    return '#6b7280';
  };

  const getMomentumBarColor = (value: number) => {
    if (value > 0.05) return '#22c55e';
    if (value < -0.05) return '#ef4444';
    return '#6b7280';
  };

  const getConfidenceColor = (value: number) => {
    if (value >= 70) return '#22c55e';
    if (value >= 50) return '#eab308';
    return '#ef4444';
  };

  const getRegimeBadge = (regime: string) => {
    const normalized = regime.toLowerCase().replace(/ /g, '_');
    const color = REGIME_COLORS[normalized as keyof typeof REGIME_COLORS] || '#6b7280';
    const label = regime;
    const icon = getRegimeIconFromString(regime);
    return { color, label, icon };
  };

  const getRegimeIconFromString = (regime: string): string => {
    const map: Record<string, string> = {
      'EXTREME OVERHEATING': '🔴',
      'OVERHEATING': '🟠',
      'WATCHING': '🟡',
      'NEUTRAL': '🟢',
      'HOLD': '🟢',
      'EQUILIBRIUM': '🟢',
      'BUY': '🔵',
      'ALIGNED': '🔵',
      'BUY OPPORTUNITY': '🔵',
      'STRONG UNDERVALUED': '🟣',
      'CAPITULATION': '💎',
    };
    return map[regime] || '⚪';
  };

  const getNdiColor = (value: number) => {
    if (value > 2.0) return '#ef4444';
    if (value > 1.5) return '#f97316';
    if (value > 0.5) return '#eab308';
    if (value > -0.5) return '#22c55e';
    if (value > -1.5) return '#3b82f6';
    if (value > -2.0) return '#7C4DFF';
    return '#6b21a8';
  };

  const getInterpretation = (confidence: number): string => {
    if (confidence >= 90) return '✅ Very high quality signal';
    if (confidence >= 70) return '✅ Good quality signal';
    if (confidence >= 50) return 'ℹ️ Moderate quality signal';
    return '⚠️ Low quality - use caution';
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-700">
            <th className="text-left py-3 px-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Ticker</th>
            <th className="text-right py-3 px-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Price</th>
            <th className="text-left py-3 px-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Sentiment</th>
            <th className="text-left py-3 px-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Momentum</th>
            <th className="text-right py-3 px-3 text-gray-400 font-medium text-xs uppercase tracking-wider">NDI</th>
            <th className="text-left py-3 px-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Regime</th>
            <th className="text-left py-3 px-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Confidence</th>
            <th className="text-left py-3 px-3 text-gray-400 font-medium text-xs uppercase tracking-wider">Interpretation</th>
          </tr>
        </thead>
        <tbody>
          {sortedTickers.map((ticker) => {
            const ndiColor = getNdiColor(ticker.ndi);
            const regimeBadge = getRegimeBadge(ticker.regime);
            const confidenceColor = getConfidenceColor(ticker.confidence);
            const isSelected = selectedTicker === ticker.ticker;

            return (
              <tr
                key={ticker.ticker}
                onClick={() => onSelectTicker(ticker.ticker)}
                className={`border-b border-gray-800 cursor-pointer transition-colors duration-150 ${
                  isSelected ? 'bg-gray-700/50' : 'hover:bg-gray-800/50'
                }`}
              >
                <td className="py-3 px-3 font-semibold text-white">{ticker.ticker}</td>
                <td className="py-3 px-3 text-right font-mono text-white">
                  ${ticker.price?.toFixed(2) || 'N/A'}
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-white w-14 text-right">
                      {ticker.sentiment?.toFixed(3) || '0.000'}
                    </span>
                    <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${getBarWidth(ticker.sentiment)}%`,
                          backgroundColor: getSentimentBarColor(ticker.sentiment),
                        }}
                      />
                    </div>
                  </div>
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-white w-14 text-right">
                      {ticker.momentum?.toFixed(3) || '0.000'}
                    </span>
                    <div className="w-20 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${getBarWidth(ticker.momentum)}%`,
                          backgroundColor: getMomentumBarColor(ticker.momentum),
                        }}
                      />
                    </div>
                  </div>
                </td>
                <td className="py-3 px-3 text-right font-mono font-bold" style={{ color: ndiColor }}>
                  {ticker.ndi?.toFixed(3) || '0.000'}
                </td>
                <td className="py-3 px-3">
                  <span
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
                    style={{
                      backgroundColor: `${regimeBadge.color}20`,
                      color: regimeBadge.color,
                      border: `1px solid ${regimeBadge.color}30`,
                    }}
                  >
                    <span>{regimeBadge.icon}</span>
                    {regimeBadge.label}
                  </span>
                </td>
                <td className="py-3 px-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-300"
                        style={{
                          width: `${ticker.confidence || 50}%`,
                          backgroundColor: confidenceColor,
                        }}
                      />
                    </div>
                    <span className="text-white font-mono text-xs w-8 text-right">
                      {Math.round(ticker.confidence || 50)}%
                    </span>
                  </div>
                </td>
                <td className="py-3 px-3 text-xs text-gray-400">
                  {getInterpretation(ticker.confidence)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
