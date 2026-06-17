import React, { useState } from 'react';
import ExpandedRow from './ExpandedRow';

const C = {
  bg: '#0e1117',
  card: '#181f2e',
  cardBorder: 'rgba(255,255,255,0.06)',
  accent: '#6c63ff',
  green: '#10b981',
  yellow: '#f59e0b',
  red: '#ef4444',
  blue: '#3b82f6',
  text: '#e2e8f0',
  muted: '#6b7280',
  dim: '#374151',
  greenBg: 'rgba(16,185,129,0.15)',
  redBg: 'rgba(239,68,68,0.15)',
  yellowBg: 'rgba(245,158,11,0.15)',
  blueBg: 'rgba(59,130,246,0.15)',
};

interface Signal {
  ticker: string;
  ndi: number;
  regime: string;
  confidence: number;
  price: number;
  events?: string[];
  narrative?: string[];
  sentiment?: number;
  momentum?: number;
}

interface ScanTableProps {
  signals: Signal[];
}

const ScanTable: React.FC<ScanTableProps> = ({ signals }) => {
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const toggleExpand = (ticker: string) => {
    setExpandedRow(expandedRow === ticker ? null : ticker);
  };

  const getRegimeColor = (regime: string) => {
    const colors: Record<string, string> = {
      'Overheating': C.red,
      'Watching': C.yellow,
      'Fear': C.blue,
      'Aligned': C.green,
    };
    return colors[regime] || C.muted;
  };

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{
            color: C.muted,
            fontSize: 11,
            borderBottom: `1px solid ${C.cardBorder}`,
            textTransform: 'uppercase',
            letterSpacing: '0.3px',
          }}>
            <th style={{ padding: '8px 12px', textAlign: 'left' }}>Ticker</th>
            <th style={{ padding: '8px 12px', textAlign: 'left' }}>NDI</th>
            <th style={{ padding: '8px 12px', textAlign: 'left' }}>Regime</th>
            <th style={{ padding: '8px 12px', textAlign: 'left' }}>Conf</th>
            <th style={{ padding: '8px 12px', textAlign: 'left' }}>Price</th>
            <th style={{ padding: '8px 12px', textAlign: 'right' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((s) => (
            <React.Fragment key={s.ticker}>
              <tr
                style={{
                  borderBottom: expandedRow === s.ticker ? 'none' : `1px solid ${C.cardBorder}`,
                  cursor: 'pointer',
                  transition: 'background 0.15s',
                }}
                onClick={() => toggleExpand(s.ticker)}
                onMouseEnter={(e) => e.currentTarget.style.background = C.card}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <td style={{ padding: '10px 12px', fontWeight: 600, fontSize: 13 }}>
                  {s.ticker}
                </td>
                <td style={{
                  padding: '10px 12px',
                  fontWeight: 600,
                  color: getRegimeColor(s.regime),
                }}>
                  {s.ndi > 0 ? `+${s.ndi.toFixed(3)}` : s.ndi.toFixed(3)}
                </td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{
                    padding: '2px 10px',
                    borderRadius: 20,
                    fontSize: 11,
                    fontWeight: 600,
                    background: getRegimeColor(s.regime) + '20',
                    color: getRegimeColor(s.regime),
                  }}>
                    {s.regime}
                  </span>
                </td>
                <td style={{ padding: '10px 12px' }}>
                  {Math.round(s.confidence * 100)}%
                </td>
                <td style={{ padding: '10px 12px', fontFamily: 'monospace' }}>
                  ${s.price.toFixed(2)}
                </td>
                <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleExpand(s.ticker); }}
                    style={{
                      background: 'transparent',
                      border: `1px solid ${C.accent}`,
                      color: C.accent,
                      borderRadius: 4,
                      padding: '3px 10px',
                      fontSize: 11,
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.background = C.accent;
                      e.currentTarget.style.color = 'white';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.color = C.accent;
                    }}
                  >
                    {expandedRow === s.ticker ? 'Close' : 'Expand'}
                  </button>
                </td>
              </tr>
              {expandedRow === s.ticker && (
                <tr>
                  <td colSpan={6} style={{ padding: 0 }}>
                    <ExpandedRow ticker={s.ticker} baseSignal={s} />
                  </td>
                </tr>
              )}
            </React.Fragment>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ScanTable;