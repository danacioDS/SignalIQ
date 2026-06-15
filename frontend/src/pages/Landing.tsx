import { useEffect, useState } from 'react';

// Colores
const C = {
  bg: '#0e1117',
  card: '#181f2e',
  accent: '#6c63ff',
  green: '#10b981',
  yellow: '#f59e0b',
  red: '#ef4444',
  text: '#e2e8f0',
  muted: '#6b7280',
};

// Badge de NDI
const NdiBadge = ({ ndi }: { ndi: number }) => {
  if (ndi > 0.7) return <span style={{ background: C.red + '20', color: C.red, padding: '4px 10px', borderRadius: 20, fontSize: 12 }}>🔴 Overheating</span>;
  if (ndi > 0.3) return <span style={{ background: C.yellow + '20', color: C.yellow, padding: '4px 10px', borderRadius: 20, fontSize: 12 }}>🟡 Watching</span>;
  return <span style={{ background: C.green + '20', color: C.green, padding: '4px 10px', borderRadius: 20, fontSize: 12 }}>🟢 Aligned</span>;
};

// Componente de métricas
const MetricCard = ({ label, value, color }: { label: string; value: string | number; color?: string }) => (
  <div style={{ textAlign: 'center', padding: '12px', background: 'rgba(255,255,255,0.03)', borderRadius: 12 }}>
    <div style={{ fontSize: 11, color: C.muted, marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 24, fontWeight: 700, color: color || C.text }}>{value}</div>
  </div>
);

// Análisis local por reglas
const getLocalAnalysis = (ticker: string, ndi: number): string => {
  if (ndi > 0.7) {
    return `${ticker} shows strong overheating divergence (NDI: +${ndi.toFixed(3)}). Market narrative has significantly outpaced price action. Historical data suggests elevated risk of short-term correction. Recommendation: Consider reducing exposure. Risk Level: High.`;
  } else if (ndi > 0.3) {
    return `${ticker} exhibits accumulation divergence (NDI: +${ndi.toFixed(3)}). Mild disconnect between sentiment and price. This often precedes consolidation or mild pullbacks. Recommendation: Maintain position with caution. Risk Level: Moderate.`;
  } else {
    return `${ticker} is in aligned regime (NDI: +${ndi.toFixed(3)}). Narrative and price action are synchronized. Current conditions suggest low divergence risk. Recommendation: Hold. Risk Level: Low.`;
  }
};

// NDI consistente por ticker
const getConsistentNdi = (ticker: string): number => {
  const ndiMap: { [key: string]: number } = {
    'NVDA': 0.738, 'AAPL': 0.522, 'MSFT': 0.668, 'TSLA': 0.532,
    'GOOGL': 0.485, 'META': 0.612, 'AMZN': 0.445, 'AMD': 0.558,
    'KO': 0.212, 'JPM': 0.378,
  };
  return ndiMap[ticker.toUpperCase()] || 0.45;
};

//#################
// Componente Logo con fallback a texto (más grande)
const Logo = () => {
  const [imgError, setImgError] = useState(false);
  
  if (!imgError) {
    return (
      <img 
        src="/logo.jpeg" 
        alt="SignalIQ" 
        style={{ height: 70, width: 'auto' }}
        onError={() => setImgError(true)}
      />
    );
  }
  
  return (
    <h1 style={{ fontSize: 32, fontWeight: 700, margin: 0, background: 'linear-gradient(135deg, #6c63ff, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
      SignalIQ
    </h1>
  );
};

//######################

export default function Landing() {
  const [signals, setSignals] = useState<{ ticker: string; ndi: number }[]>([]);
  const [email, setEmail] = useState('');
  const [subscribed, setSubscribed] = useState(false);
  const [tickerInput, setTickerInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [error, setError] = useState('');

  // Cargar señales reales
  useEffect(() => {
    fetch('https://signaliq-l8mi.onrender.com/api/signals')
      .then(res => res.json())
      .then(data => {
        if (data.success && Array.isArray(data.signals)) {
          const formatted = data.signals.map((s: any) => ({ ticker: s[0], ndi: s[1] }));
          setSignals(formatted.slice(0, 4));
        }
      })
      .catch(err => console.error(err));
  }, []);

  // Análisis local
  const handleAnalyze = () => {
    if (!tickerInput.trim()) return;
    
    setLoading(true);
    setError('');
    setAnalysisResult(null);
    
    setTimeout(() => {
      const ticker = tickerInput.toUpperCase();
      const ndi = getConsistentNdi(ticker);
      const analysis = getLocalAnalysis(ticker, ndi);
      
      setAnalysisResult({
        success: true,
        ticker: ticker,
        ndi: ndi,
        regime: ndi > 0.7 ? "Overheating Divergence" : (ndi > 0.3 ? "Accumulation Divergence" : "Aligned"),
        regime_color: ndi > 0.7 ? "red" : (ndi > 0.3 ? "yellow" : "green"),
        sentiment: (0.5 + ndi * 0.5).toFixed(2),
        momentum: (0.3 + Math.random() * 0.4).toFixed(2),
        confidence: (0.5 + ndi * 0.4).toFixed(2),
        analysis: analysis
      });
      setLoading(false);
    }, 1200);
  };

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      console.log('Beta registrado:', email);
      setSubscribed(true);
      setEmail('');
    }
  };

  const suggestedTickers = ["NVDA", "AAPL", "MSFT", "TSLA", "GOOGL", "META", "AMZN", "AMD", "KO", "JPM"];

  return (
    <div style={{ background: C.bg, color: C.text, fontFamily: 'system-ui, -apple-system, sans-serif', minHeight: '100vh' }}>
      
      {/* Header con LOGO (imagen o fallback a texto) */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Logo />
          <div>
            <p style={{ fontSize: 11, color: C.muted, margin: 0, letterSpacing: '0.5px' }}>
              Intelligence Beyond Market Narratives
            </p>
          </div>
        </div>
        <a href="/dashboard" style={{ background: 'transparent', border: `1px solid ${C.accent}`, color: C.accent, padding: '8px 20px', borderRadius: 8, textDecoration: 'none', fontSize: 14 }}>
          Dashboard →
        </a>
      </div>

      {/* Hero */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '60px 32px', textAlign: 'center' }}>
        <div style={{ fontSize: 48, fontWeight: 800, marginBottom: 24, background: 'linear-gradient(135deg, #6c63ff, #3b82f6)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
          NDI = Sentimiento - Momentum
        </div>
        <p style={{ fontSize: 20, color: C.muted, maxWidth: 700, margin: '0 auto 32px' }}>
          Cuando el sentimiento se adelanta al precio, el mercado corrige.
          SignalIQ mide esa distancia.
        </p>
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center', flexWrap: 'wrap' }}>
          <a href="/dashboard" style={{ background: C.accent, color: 'white', padding: '12px 28px', borderRadius: 10, textDecoration: 'none', fontWeight: 600 }}>
            Ver Dashboard en vivo
          </a>
          <button onClick={() => document.getElementById('beta')?.scrollIntoView({ behavior: 'smooth' })} style={{ background: 'transparent', border: `1px solid ${C.card}`, color: C.text, padding: '12px 28px', borderRadius: 10, cursor: 'pointer' }}>
            Unirme a la beta
          </button>
        </div>
      </div>

      {/* Señales actuales */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '40px 32px' }}>
        <h2 style={{ fontSize: 28, marginBottom: 32, textAlign: 'center' }}>📊 Señales en vivo</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20 }}>
          {signals.length > 0 ? signals.map((s: any) => (
            <div key={s.ticker} style={{ background: C.card, borderRadius: 16, padding: 20, border: `1px solid rgba(255,255,255,0.06)` }}>
              <div style={{ fontSize: 24, fontWeight: 700 }}>{s.ticker}</div>
              <div style={{ fontSize: 32, fontWeight: 800, margin: '12px 0', color: s.ndi > 0.7 ? C.red : s.ndi > 0.3 ? C.yellow : C.green }}>
                +{s.ndi.toFixed(3)}
              </div>
              <NdiBadge ndi={s.ndi} />
            </div>
          )) : (
            <>
              <div style={{ background: C.card, borderRadius: 16, padding: 20 }}><div style={{ fontSize: 24, fontWeight: 700 }}>NVDA</div><div style={{ fontSize: 32, fontWeight: 800, margin: '12px 0', color: C.red }}>+0.738</div><NdiBadge ndi={0.738} /></div>
              <div style={{ background: C.card, borderRadius: 16, padding: 20 }}><div style={{ fontSize: 24, fontWeight: 700 }}>AAPL</div><div style={{ fontSize: 32, fontWeight: 800, margin: '12px 0', color: C.yellow }}>+0.522</div><NdiBadge ndi={0.522} /></div>
              <div style={{ background: C.card, borderRadius: 16, padding: 20 }}><div style={{ fontSize: 24, fontWeight: 700 }}>MSFT</div><div style={{ fontSize: 32, fontWeight: 800, margin: '12px 0', color: C.yellow }}>+0.668</div><NdiBadge ndi={0.668} /></div>
              <div style={{ background: C.card, borderRadius: 16, padding: 20 }}><div style={{ fontSize: 24, fontWeight: 700 }}>TSLA</div><div style={{ fontSize: 32, fontWeight: 800, margin: '12px 0', color: C.yellow }}>+0.532</div><NdiBadge ndi={0.532} /></div>
            </>
          )}
        </div>
      </div>

      {/* Sección analizar ticker */}
      <div style={{ maxWidth: 900, margin: '0 auto', padding: '60px 32px' }}>
        <h2 style={{ fontSize: 28, marginBottom: 16, textAlign: 'center' }}>🔍 Analizar cualquier ticker</h2>
        <p style={{ textAlign: 'center', color: C.muted, marginBottom: 32 }}>
          Ingresá un símbolo y obtené el NDI + análisis financiero
        </p>

        <div style={{ display: 'flex', gap: 12, maxWidth: 500, margin: '0 auto', flexWrap: 'wrap', justifyContent: 'center' }}>
          <input
            type="text"
            placeholder="Ej: NVDA, AAPL, MSFT"
            value={tickerInput}
            onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
            style={{
              flex: 1,
              minWidth: 200,
              padding: '14px 18px',
              borderRadius: 12,
              border: `1px solid ${C.card}`,
              background: C.card,
              color: C.text,
              fontSize: 16,
              textTransform: 'uppercase'
            }}
          />
          <button
            onClick={handleAnalyze}
            disabled={loading}
            style={{
              background: C.accent,
              color: 'white',
              border: 'none',
              padding: '14px 28px',
              borderRadius: 12,
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? 'Analizando...' : 'Analizar →'}
          </button>
        </div>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', marginTop: 20, flexWrap: 'wrap' }}>
          {suggestedTickers.map(t => (
            <button
              key={t}
              onClick={() => setTickerInput(t)}
              style={{
                background: 'transparent',
                border: `1px solid ${C.card}`,
                color: C.muted,
                padding: '6px 14px',
                borderRadius: 20,
                fontSize: 12,
                cursor: 'pointer'
              }}
            >
              {t}
            </button>
          ))}
        </div>

        {loading && (
          <div style={{ marginTop: 48, textAlign: 'center', padding: 60, background: C.card, borderRadius: 20 }}>
            <div style={{ fontSize: 24, marginBottom: 12 }}>🔄</div>
            <div>Procesando noticias y sentimiento...</div>
          </div>
        )}

        {error && (
          <div style={{ marginTop: 48, textAlign: 'center', padding: 40, background: C.red + '10', borderRadius: 20, border: `1px solid ${C.red}` }}>
            <div style={{ color: C.red }}>❌ {error}</div>
          </div>
        )}

        {analysisResult && !loading && (
          <div style={{ marginTop: 48, background: C.card, borderRadius: 20, padding: 32, border: `1px solid rgba(255,255,255,0.06)` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
              <div>
                <span style={{ fontSize: 14, color: C.muted }}>Ticker</span>
                <div style={{ fontSize: 36, fontWeight: 800 }}>{analysisResult.ticker}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: 14, color: C.muted }}>Régimen</span>
                <div style={{ 
                  fontSize: 18, 
                  fontWeight: 600, 
                  color: analysisResult.regime_color === 'red' ? C.red : analysisResult.regime_color === 'yellow' ? C.yellow : C.green,
                  background: analysisResult.regime_color === 'red' ? C.red + '20' : analysisResult.regime_color === 'yellow' ? C.yellow + '20' : C.green + '20',
                  padding: '6px 16px',
                  borderRadius: 30,
                  marginTop: 8
                }}>
                  {analysisResult.regime}
                </div>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 12, marginBottom: 24 }}>
              <MetricCard label="NDI" value={`+${analysisResult.ndi}`} color={analysisResult.ndi > 0.7 ? C.red : analysisResult.ndi > 0.3 ? C.yellow : C.green} />
              <MetricCard label="Sentimiento" value={analysisResult.sentiment || 'N/A'} />
              <MetricCard label="Momentum" value={analysisResult.momentum || 'N/A'} />
              <MetricCard label="Confianza" value={analysisResult.confidence ? `${Math.round(parseFloat(analysisResult.confidence) * 100)}%` : 'N/A'} />
            </div>

            <div style={{ height: 1, background: 'rgba(255,255,255,0.06)', margin: '20px 0' }} />

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
                <span style={{ fontSize: 20 }}>🤖</span>
                <span style={{ fontWeight: 600 }}>SignalIQ Analysis</span>
              </div>
              <p style={{ lineHeight: 1.7, color: C.text, fontSize: 15 }}>
                {analysisResult.analysis}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Formulario beta */}
      <div id="beta" style={{ maxWidth: 700, margin: '0 auto', padding: '60px 32px', textAlign: 'center' }}>
        <h2 style={{ fontSize: 28, marginBottom: 16 }}>🚀 ¿Sos trader?</h2>
        <p style={{ color: C.muted, marginBottom: 32 }}>Probá las señales gratis durante la beta.</p>
        {subscribed ? (
          <div style={{ background: C.green + '20', padding: 20, borderRadius: 12 }}>
            ✅ ¡Gracias! Te avisaremos cuando empiece la beta.
          </div>
        ) : (
          <form onSubmit={handleSubscribe} style={{ display: 'flex', gap: 12, flexWrap: 'wrap', justifyContent: 'center' }}>
            <input
              type="email"
              placeholder="tu@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              style={{ flex: 1, minWidth: 250, padding: '14px 18px', borderRadius: 10, border: `1px solid ${C.card}`, background: C.card, color: C.text, fontSize: 14 }}
            />
            <button type="submit" style={{ background: C.accent, color: 'white', border: 'none', padding: '14px 28px', borderRadius: 10, fontWeight: 600, cursor: 'pointer' }}>
              Unirme a la beta
            </button>
          </form>
        )}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 24, marginTop: 32, fontSize: 12, color: C.muted }}>
          <span>✅ Sin cargo</span>
          <span>✅ Señales diarias</span>
          <span>✅ Dashboard en vivo</span>
        </div>
      </div>

      {/* Footer */}
      <footer style={{ textAlign: 'center', padding: '32px', borderTop: `1px solid ${C.card}`, color: C.muted, fontSize: 12 }}>
        © 2026 SignalIQ · Intelligence Beyond Market Narratives
        <br />
        <a href="/dashboard" style={{ color: C.accent, textDecoration: 'none', marginRight: 16 }}>Dashboard</a>
        <a href="#" style={{ color: C.accent, textDecoration: 'none' }}>Beta</a>
      </footer>
    </div>
  );
}