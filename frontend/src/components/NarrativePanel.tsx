import React from 'react';
import { C } from './styles';
import { getRegimeColor, getRegimeIcon } from '../utils/velocimeterUtils';

interface NarrativePanelProps {
  ticker: string;
  ndi: number;
  regime: string;
  sentiment: number;
  momentum: number;
  price: number;
  explanation: {
    paragraph1: string;
    paragraph2: string;
    marketInsight: string;
    riskContext: string;
  };
}

export const NarrativePanel: React.FC<NarrativePanelProps> = ({
  ticker,
  ndi,
  regime,
  sentiment,
  momentum,
  price,
  explanation,
}) => {
  const color = getRegimeColor(regime as any);
  const icon = getRegimeIcon(regime as any);

  return (
    <div
      style={{
        background: C.card,
        border: '1px solid ' + C.cardBorder,
        borderRadius: 12,
        padding: 24,
        marginTop: 16,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 18, fontWeight: 700, color: C.text }}>
            🤖 {ticker}
          </span>
          <span
            style={{
              fontSize: 12,
              background: color + '20',
              color: color,
              padding: '2px 12px',
              borderRadius: 20,
              fontWeight: 600,
            }}
          >
            {icon} {regime.replace('_', ' ')}
          </span>
        </div>
        <span style={{ fontSize: 12, color: C.muted }}>
          NDI: {ndi > 0 ? '+' + ndi.toFixed(3) : ndi.toFixed(3)}
        </span>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 12,
          marginBottom: 16,
          padding: 12,
          background: C.bg,
          borderRadius: 8,
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: C.muted }}>Sentiment</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
            {sentiment.toFixed(3)}
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: C.muted }}>Momentum</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
            {momentum.toFixed(2)}%
          </div>
        </div>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 10, color: C.muted }}>Price</div>
          <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>
            ${typeof price === 'number' ? price.toFixed(2) : price}
          </div>
        </div>
      </div>

      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, color: C.muted, marginBottom: 8 }}>
          🧠 Market Analysis
        </div>
        <p style={{ fontSize: 13, lineHeight: 1.7, color: C.text, marginBottom: 8 }}>
          {explanation.paragraph1}
        </p>
        <p style={{ fontSize: 13, lineHeight: 1.7, color: C.text, marginBottom: 0 }}>
          {explanation.paragraph2}
        </p>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: 16,
          marginTop: 12,
          paddingTop: 12,
          borderTop: '1px solid ' + C.cardBorder,
        }}
      >
        <div>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>
            📊 Market Insight
          </div>
          <p style={{ fontSize: 12, lineHeight: 1.5, color: C.text, margin: 0 }}>
            {explanation.marketInsight}
          </p>
        </div>
        <div>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>
            ⚠️ Risk Context
          </div>
          <p style={{ fontSize: 12, lineHeight: 1.5, color: C.text, margin: 0 }}>
            {explanation.riskContext}
          </p>
        </div>
      </div>
    </div>
  );
};

export default NarrativePanel;
