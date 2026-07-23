import React, { useState, useEffect } from 'react';

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

interface ExpandedRowProps {
  ticker: string;
  baseSignal?: any;
}

interface IntelData {
  ndi: number;
  events: string[];
  narrative: string[];
  timestamp: string;
}

const ExpandedRow: React.FC<ExpandedRowProps> = ({ ticker, baseSignal }) => {
  const [intel, setIntel] = useState<IntelData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchIntel = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(
          `https://signaliq-api.onrender.com/api/signals-intel?ticker=${ticker}`
        );
        
        if (!response.ok) {
          if (response.status === 404) {
            throw new Error(`No intelligence data found for ${ticker}`);
          }
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        if (data.success) {
          setIntel({
            ndi: data.ndi || 0,
            events: data.events || [],
            narrative: data.narrative || [],
            timestamp: data.timestamp || new Date().toISOString(),
          });
        } else {
          throw new Error(data.error || 'Unknown error');
        }
      } catch (err) {
        console.error('Error fetching intel:', err);
        setError(err instanceof Error ? err.message : 'Failed to load intelligence');
        if (baseSignal) {
          setIntel({
            ndi: baseSignal.ndi || 0,
            events: ['Data unavailable'],
            narrative: ['No intelligence data available for this ticker'],
            timestamp: new Date().toISOString(),
          });
        }
      } finally {
        setLoading(false);
      }
    };

    fetchIntel();
  }, [ticker, baseSignal]);

  const impact = intel?.ndi && intel.ndi > 0.7 
    ? 'Market pricing narrative ahead of price movement' 
    : intel?.ndi && intel.ndi < -0.5 
      ? 'Price movement ahead of narrative' 
      : 'Narrative and price are aligned';

  const getImplication = () => {
    if (!intel?.ndi) return 'Neutral';
    if (intel.ndi > 0.7) return 'Bearish pressure';
    if (intel.ndi < -0.5) return 'Bullish opportunity';
    return 'Neutral';
  };

  const getImplicationColor = () => {
    if (!intel?.ndi) return C.yellow;
    if (intel.ndi > 0.7) return C.red;
    if (intel.ndi < -0.5) return C.green;
    return C.yellow;
  };

  const getImplicationBg = () => {
    if (!intel?.ndi) return C.yellowBg;
    if (intel.ndi > 0.7) return C.redBg;
    if (intel.ndi < -0.5) return C.greenBg;
    return C.yellowBg;
  };

  if (loading) {
    return (
      <div style={{
        background: C.bg,
        padding: '16px 20px',
        borderBottom: `1px solid ${C.cardBorder}`,
        margin: '0 12px',
        borderRadius: '0 0 8px 8px',
        textAlign: 'center',
        color: C.muted,
      }}>
        <span style={{ fontSize: 13 }}>🔄 Loading intelligence for {ticker}...</span>
      </div>
    );
  }

  if (error && !intel) {
    return (
      <div style={{
        background: C.bg,
        padding: '16px 20px',
        borderBottom: `1px solid ${C.cardBorder}`,
        margin: '0 12px',
        borderRadius: '0 0 8px 8px',
        textAlign: 'center',
        color: C.muted,
      }}>
        <span style={{ fontSize: 13, color: C.red }}>⚠️ {error}</span>
      </div>
    );
  }

  if (!intel) {
    return null;
  }

  return (
    <div style={{
      background: C.bg,
      padding: '16px 20px',
      borderBottom: `1px solid ${C.cardBorder}`,
      margin: '0 12px',
      borderRadius: '0 0 8px 8px',
    }}>
      <p style={{
        fontSize: 13,
        color: C.text,
        marginBottom: 14,
        fontWeight: 500,
        paddingLeft: 4,
      }}>
        {impact}
      </p>

      {intel.events && intel.events.length > 0 && (
        <div style={{ marginBottom: 10 }}>
          <p style={{
            fontSize: 10,
            color: C.muted,
            marginBottom: 4,
            fontWeight: 600,
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
          }}>
            Events
          </p>
          <ul style={{
            fontSize: 12,
            lineHeight: 1.6,
            color: C.text,
            margin: 0,
            paddingLeft: 18,
            listStyleType: 'disc',
          }}>
            {intel.events.slice(0, 3).map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {intel.narrative && intel.narrative.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <p style={{
            fontSize: 10,
            color: C.muted,
            marginBottom: 4,
            fontWeight: 600,
            letterSpacing: '0.5px',
            textTransform: 'uppercase',
          }}>
            Narrative
          </p>
          <ul style={{
            fontSize: 12,
            lineHeight: 1.6,
            color: C.text,
            margin: 0,
            paddingLeft: 18,
            listStyleType: 'disc',
          }}>
            {intel.narrative.slice(0, 3).map((item, i) => (
              <li key={i}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(80px, 1fr))',
        gap: 8,
        marginBottom: 12,
      }}>
        <div style={{
          background: C.card,
          borderRadius: 6,
          padding: '6px 10px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: 10, color: C.muted }}>NDI</div>
          <div style={{ fontSize: 14, fontWeight: 600 }}>
            {intel.ndi > 0 ? `+${intel.ndi.toFixed(3)}` : intel.ndi.toFixed(3)}
          </div>
        </div>
      </div>

      <div style={{
        display: 'inline-block',
        padding: '4px 12px',
        borderRadius: 20,
        background: getImplicationBg(),
        marginBottom: 12,
      }}>
        <span style={{
          fontSize: 12,
          fontWeight: 600,
          color: getImplicationColor(),
        }}>
          {getImplication()}
        </span>
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        <button style={{
          background: C.accent,
          color: 'white',
          border: 'none',
          padding: '4px 12px',
          borderRadius: 4,
          fontSize: 11,
          cursor: 'pointer',
        }}>
          Alert
        </button>
        <button style={{
          background: 'transparent',
          border: `1px solid ${C.cardBorder}`,
          color: C.text,
          padding: '4px 12px',
          borderRadius: 4,
          fontSize: 11,
          cursor: 'pointer',
        }}>
          Track
        </button>
        <button style={{
          background: 'transparent',
          border: `1px solid ${C.cardBorder}`,
          color: C.text,
          padding: '4px 12px',
          borderRadius: 4,
          fontSize: 11,
          cursor: 'pointer',
        }}>
          Export
        </button>
      </div>
    </div>
  );
};

export default ExpandedRow;