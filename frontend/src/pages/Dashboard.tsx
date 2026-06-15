import { useEffect, useState } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend
} from 'recharts';

// Colores
const C = {
  bg: '#0e1117',
  card: '#181f2e',
  cardBorder: 'rgba(255,255,255,0.06)',
  accent: '#6c63ff',
  green: '#10b981',
  yellow: '#f59e0b',
  red: '#ef4444',
  text: '#e2e8f0',
  muted: '#6b7280',
  dim: '#374151',
};

// Badge de estado
const StatusBadge = ({ ndi }: { ndi: number }) => {
  if (ndi > 0.7) return <span style={{ background: C.red + '20', color: C.red, padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600 }}>🔴 OVERHEATING</span>;
  if (ndi > 0.3) return <span style={{ background: C.yellow + '20', color: C.yellow, padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600 }}>🟡 WATCHING</span>;
  return <span style={{ background: C.green + '20', color: C.green, padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600 }}>🟢 ALIGNED</span>;
};

// KPI Card
const KPICard = ({ title, value, change, positive, icon }: { title: string; value: string; change?: string; positive?: boolean; icon: string }) => (
  <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 16, padding: '20px' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
      <span style={{ fontSize: 13, color: C.muted }}>{icon} {title}</span>
      <span style={{ fontSize: 18, color: C.muted }}>···</span>
    </div>
    <div style={{ fontSize: 28, fontWeight: 700, color: C.text }}>{value}</div>
    {change && (
      <div style={{ fontSize: 12, marginTop: 8, color: positive ? C.green : C.red }}>
        {positive ? '▲' : '▼'} {change} vs ayer
      </div>
    )}
  </div>
);

// Análisis local
const getAnalysis = (ticker: string, ndi: number): string => {
  if (ndi > 0.7) {
    return `${ticker} shows strong overheating divergence. Consider reducing exposure.`;
  } else if (ndi > 0.3) {
    return `${ticker} exhibits accumulation divergence. Maintain position with caution.`;
  } else {
    return `${ticker} is in aligned regime. Hold position.`;
  }
};

const getNdiForTicker = (ticker: string): number => {
  const ndiMap: Record<string, number> = {
    'NVDA': 0.738, 'AAPL': 0.522, 'MSFT': 0.668, 'TSLA': 0.532,
    'GOOGL': 0.485, 'META': 0.612, 'AMZN': 0.445, 'AMD': 0.558,
    'KO': 0.212, 'JPM': 0.378,
  };
  return ndiMap[ticker] || 0.45;
};

const generateHistoricalData = () => {
  const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun'];
  return months.map((month, i) => ({
    month,
    NVDA: 0.5 + Math.random() * 0.4,
    AAPL: 0.4 + Math.random() * 0.3,
    MSFT: 0.45 + Math.random() * 0.35,
    TSLA: 0.4 + Math.random() * 0.5,
  }));
};

export default function Dashboard() {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [historicalData] = useState(generateHistoricalData());

  useEffect(() => {
    fetch('https://signaliq-l8mi.onrender.com/api/signals')
      .then(res => res.json())
      .then(data => {
        if (data.success && Array.isArray(data.signals)) {
          const formatted = data.signals.map((s: any) => ({
            ticker: s[0],
            ndi: s[1] / 100,
            direction: s[2],
            strength: s[3],
            recommendation: s[4],
            price: s[5],
            lastUpdated: s[6],
          }));
          setSignals(formatted);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const allTickers = [
    ...signals,
    { ticker: 'GOOGL', ndi: getNdiForTicker('GOOGL') },
    { ticker: 'META', ndi: getNdiForTicker('META') },
    { ticker: 'AMZN', ndi: getNdiForTicker('AMZN') },
    { ticker: 'AMD', ndi: getNdiForTicker('AMD') },
    { ticker: 'KO', ndi: getNdiForTicker('KO') },
    { ticker: 'JPM', ndi: getNdiForTicker('JPM') },
  ].filter((v, i, a) => a.findIndex(t => t.ticker === v.ticker) === i);

  const avgNdi = (allTickers.reduce((sum, t) => sum + t.ndi, 0) / allTickers.length).toFixed(3);
  const activeSignals = allTickers.filter(t => t.ndi > 0.3).length;
  const overheatingCount = allTickers.filter(t => t.ndi > 0.7).length;
  const avgConfidence = (allTickers.reduce((sum, t) => sum + (0.5 + t.ndi * 0.4), 0) / allTickers.length * 100).toFixed(0);

  return (
    <div style={{ background: C.bg, minHeight: '100vh', color: C.text, fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      
      {/* Header */}
      <div style={{ borderBottom: `1px solid ${C.cardBorder}`, padding: '20px 32px' }}>
        <div style={{ maxWidth: 1400, margin: '0 auto', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, margin: 0 }}>📊 SignalIQ Dashboard</h1>
            <p style={{ fontSize: 13, color: C.muted, margin: '4px 0 0' }}>Narrative Divergence Intelligence · Señales en tiempo real</p>
          </div>
          <div style={{ display: 'flex', gap: 12 }}>
            <a href="/" style={{ background: 'transparent', border: `1px solid ${C.accent}`, color: C.accent, padding: '8px 18px', borderRadius: 8, textDecoration: 'none', fontSize: 13 }}>
              ← Volver a la landing
            </a>
            <button onClick={() => window.location.reload()} style={{ background: C.accent, border: 'none', color: 'white', padding: '8px 18px', borderRadius: 8, fontSize: 13, cursor: 'pointer' }}>
              🔄 Actualizar
            </button>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '32px' }}>
        
        {/* KPIs */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20, marginBottom: 32 }}>
          <KPICard icon="📊" title="NDI Promedio" value={avgNdi} change="+2.3%" positive={false} />
          <KPICard icon="🟡" title="Señales Activas" value={activeSignals.toString()} change="+1" positive={true} />
          <KPICard icon="🔴" title="Overheating" value={overheatingCount.toString()} />
          <KPICard icon="🎯" title="Confianza Promedio" value={`${avgConfidence}%`} change="+5%" positive={true} />
        </div>

        {/* Gráfico */}
        <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 16, padding: '24px', marginBottom: 32 }}>
          <h3 style={{ fontSize: 16, marginBottom: 20, fontWeight: 600 }}>📈 Evolución del NDI (últimos 6 meses)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={historicalData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.dim} />
              <XAxis dataKey="month" stroke={C.muted} />
              <YAxis stroke={C.muted} domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} />
              <Tooltip contentStyle={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 8 }} />
              <Legend />
              <Line type="monotone" dataKey="NVDA" stroke={C.red} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="AAPL" stroke={C.yellow} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="MSFT" stroke={C.accent} strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="TSLA" stroke={C.green} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Tabla de señales */}
        <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 16, overflow: 'hidden' }}>
          <div style={{ padding: '20px 24px', borderBottom: `1px solid ${C.cardBorder}` }}>
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>📋 Señales por Ticker</h3>
          </div>
          
          {loading ? (
            <div style={{ padding: '60px', textAlign: 'center', color: C.muted }}>Cargando señales...</div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: `1px solid ${C.cardBorder}`, color: C.muted, fontSize: 12 }}>
                    <th style={{ textAlign: 'left', padding: '16px 20px' }}>Ticker</th>
                    <th style={{ textAlign: 'left', padding: '16px 20px' }}>NDI</th>
                    <th style={{ textAlign: 'left', padding: '16px 20px' }}>Régimen</th>
                    <th style={{ textAlign: 'left', padding: '16px 20px' }}>Dirección</th>
                    <th style={{ textAlign: 'left', padding: '16px 20px' }}>Confianza</th>
                    <th style={{ textAlign: 'left', padding: '16px 20px' }}>Recomendación</th>
                    <th style={{ textAlign: 'left', padding: '16px 20px' }}>Precio</th>
                  </tr>
                </thead>
                <tbody>
                  {allTickers.map((signal, idx) => {
                    const ndi = signal.ndi;
                    const confidence = Math.round((0.5 + ndi * 0.4) * 100);
                    return (
                      <tr key={idx} style={{ borderBottom: `1px solid ${C.cardBorder}`, fontSize: 13 }}>
                        <td style={{ padding: '14px 20px', fontWeight: 600 }}>{signal.ticker}</td>
                        <td style={{ padding: '14px 20px', color: ndi > 0.7 ? C.red : ndi > 0.3 ? C.yellow : C.green, fontWeight: 600 }}>
                          +{ndi.toFixed(3)}
                        </td>
                        <td style={{ padding: '14px 20px' }}><StatusBadge ndi={ndi} /></td>
                        <td style={{ padding: '14px 20px', color: signal.direction === 'BULLISH' ? C.green : C.muted }}>
                          {signal.direction || 'NEUTRAL'}
                        </td>
                        <td style={{ padding: '14px 20px' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span>{confidence}%</span>
                            <div style={{ flex: 1, height: 4, background: C.dim, borderRadius: 2, maxWidth: 60 }}>
                              <div style={{ width: `${confidence}%`, height: 4, background: C.accent, borderRadius: 2 }} />
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: '14px 20px', color: C.muted, maxWidth: 200 }}>
                          {signal.recommendation ? signal.recommendation.substring(0, 60) : getAnalysis(signal.ticker, ndi).substring(0, 60)}...
                        </td>
                        <td style={{ padding: '14px 20px', fontFamily: 'monospace' }}>${signal.price?.toFixed(2) || 'N/A'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          
          <div style={{ padding: '16px 20px', borderTop: `1px solid ${C.cardBorder}`, fontSize: 11, color: C.muted }}>
            Última actualización: {new Date().toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}
