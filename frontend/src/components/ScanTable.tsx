import React, { useState } from 'react';
import ExpandedRow from './ExpandedRow';
import { C } from './styles';

interface Signal {
  ticker: string;
  ndi: number;
  regime: string;
  confidence: number;
  price: number;
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

  const getRegimeIcon = (regime: string) => {
    const icons: Record<string, string> = {
      'Overheating': '🔴',
      'Watching': '🟡',
      'Fear': '📉',
      'Aligned': '🟢',
    };
    return icons[regime] || '🟡';
  };

  return (
    <div>
      {/* Grid de tarjetas */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', 
        gap: '14px',
        marginBottom: '16px'
      }}>
        {signals.map((s) => {
          const isExpanded = expandedRow === s.ticker;
          return (
            <div key={s.ticker}>
              <div 
                style={{
                  background: C.card,
                  border: `1px solid ${isExpanded ? C.accent : C.cardBorder}`,
                  borderRadius: 12,
                  padding: '16px 18px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  position: 'relative',
                  overflow: 'hidden',
                }}
                onClick={() => toggleExpand(s.ticker)}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor = C.accent; }}
                onMouseLeave={(e) => { if (!isExpanded) e.currentTarget.style.borderColor = C.cardBorder; }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 18, fontWeight: 700 }}>{s.ticker}</span>
                  <span style={{ fontSize: 11, color: C.muted }}>{s.regime}</span>
                </div>
                <div style={{ 
                  fontSize: 28, 
                  fontWeight: 700, 
                  margin: '4px 0', 
                  color: getRegimeColor(s.regime) 
                }}>
                  {s.ndi > 0 ? `+${s.ndi.toFixed(3)}` : s.ndi.toFixed(3)}
                </div>
                <div style={{ 
                  display: 'inline-block',
                  fontSize: 11, 
                  background: getRegimeColor(s.regime) + '20', 
                  color: getRegimeColor(s.regime), 
                  padding: '2px 10px', 
                  borderRadius: 20,
                  fontWeight: 600,
                }}>
                  {getRegimeIcon(s.regime)} {s.regime}
                </div>
                <div style={{ fontSize: 12, color: C.muted, marginTop: 6 }}>
                  ${s.price.toFixed(2)}
                </div>
                <div style={{ 
                  position: 'absolute', 
                  bottom: 0, 
                  left: 0, 
                  right: 0, 
                  height: 2, 
                  background: getRegimeColor(s.regime),
                  opacity: 0.3,
                }} />
              </div>
              
              {/* ExpandedRow - se muestra debajo de la card */}
              {isExpanded && (
                <div style={{ marginTop: '8px' }}>
                  <ExpandedRow ticker={s.ticker} baseSignal={s} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ScanTable;
