import { useState, useEffect } from "react";
import { C } from "../components/styles";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  getRegimeFromNdi,
  getRegimeLabel,
  getRegimeIcon,
  getRegimeColor,
  getRegimeBg,
} from "../utils/regimeHelpers";

// ── Sector colors ─────────────────────────────────────────────────────────────
const sectorColors: Record<string, string> = {
  'Technology': '#6c63ff',
  'Automotive': '#f59e0b',
  'Financial': '#3b82f6',
  'Energy': '#10b981',
  'Consumer': '#ef4444',
  'Healthcare': '#8b5cf6',
  'Semiconductors': '#ec4899',
};

export default function Dashboard() {
  const [selectedSector, setSelectedSector] = useState("All");
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tickerInput, setTickerInput] = useState("");
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [priceHistory, setPriceHistory] = useState<any[]>([]);
  const [selectedTicker, setSelectedTicker] = useState("");

  // ── Mapeo de sectores ──────────────────────────────────────────────────────
  const sectorMap: Record<string, string> = {
    'NVDA': 'Technology', 'AAPL': 'Technology', 'MSFT': 'Technology',
    'GOOGL': 'Technology', 'META': 'Technology', 'AMD': 'Technology',
    'AMZN': 'Technology', 'TSLA': 'Automotive', 'JPM': 'Financial',
    'BAC': 'Financial', 'GS': 'Financial', 'XOM': 'Energy',
    'CVX': 'Energy', 'COP': 'Energy', 'KO': 'Consumer',
    'WMT': 'Consumer', 'PG': 'Consumer', 'JNJ': 'Healthcare',
    'UNH': 'Healthcare', 'TSM': 'Semiconductors', 'INTC': 'Semiconductors'
  };

  const defaultTickers = ['NVDA', 'AAPL', 'MSFT', 'TSLA', 'GOOGL', 'META', 'AMD', 'AMZN', 'JPM', 'XOM', 'KO'];

  // ── Cargar datos desde la API ──────────────────────────────────────────────
  useEffect(() => {
    const fetchSignals = async () => {
      try {
        setLoading(true);
        setError("");
        const response = await fetch(
          `https://signaliq-api.onrender.com/api/signals-live?tickers=${defaultTickers.join(',')}`
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        
        if (data.success && data.signals && data.signals.length > 0) {
          const formatted = data.signals.map((item: any) => {
            const ndi = item.ndi || 0;
            return {
              ticker: item.ticker,
              ndi: ndi,
              sector: sectorMap[item.ticker] || 'Other',
              price: item.current_price || 'N/A',
              sentiment: item.sentiment || 0,
              momentum: item.momentum || 0,
              confidence: item.confidence || 70,
            };
          });
          setSignals(formatted);
          if (formatted.length > 0) {
            setSelectedTicker(formatted[0].ticker);
          }
        } else {
          setError("No data available from the API.");
          setSignals([]);
        }
      } catch (err) {
        console.error('Error fetching signals:', err);
        setError('⚠️ Could not load market data. Check your connection.');
        setSignals([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSignals();
    const interval = setInterval(fetchSignals, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // ── Calcular métricas ──────────────────────────────────────────────────────
  const sectors = ["All", ...Array.from(new Set(signals.map(s => s.sector)))];
  const filteredSignals = selectedSector === "All" 
    ? signals 
    : signals.filter(s => s.sector === selectedSector);

  const sectorAverages = signals.reduce((acc, s) => {
    if (!acc[s.sector]) acc[s.sector] = { total: 0, count: 0 };
    acc[s.sector].total += s.ndi;
    acc[s.sector].count += 1;
    return acc;
  }, {} as Record<string, { total: number; count: number }>);

  const sectorPerformance = Object.keys(sectorAverages).map(sector => ({
    sector,
    avgNDI: sectorAverages[sector].total / sectorAverages[sector].count,
    color: sectorColors[sector] || C.muted
  }));

  // ── KPIs ────────────────────────────────────────────────────────────────────
  const avgNDI = signals.length > 0 
    ? signals.reduce((sum, s) => sum + s.ndi, 0) / signals.length 
    : 0;
  const activeSignals = signals.filter(s => s.ndi > 0.5 || s.ndi < -0.5).length;
  const overheating = signals.filter(s => s.ndi > 1.5).length;
  const avgConfidence = signals.length > 0 
    ? Math.round(signals.reduce((sum, s) => sum + (s.confidence || 70), 0) / signals.length) 
    : 0;

  const KPI = ({ icon, label, value, badge, positive }: any) => (
    <div style={{
      background: C.card,
      border: `1px solid ${C.cardBorder}`,
      borderRadius: 12,
      padding: "16px 20px",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: 12, color: C.muted }}>{icon} {label}</span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginTop: 4 }}>
        <span style={{ fontSize: 24, fontWeight: 700, color: C.text }}>{value}</span>
        {badge && (
          <span style={{
            fontSize: 10,
            fontWeight: 700,
            padding: "2px 8px",
            borderRadius: 20,
            background: positive ? C.greenBg : C.redBg,
            color: positive ? C.green : C.red,
          }}>
            {positive ? "▲" : "▼"} {badge}
          </span>
        )}
      </div>
    </div>
  );

  // ── Analizar ticker desde la API ──────────────────────────────────────────
  const analyzeTicker = async (tickerOverride?: string) => {
    const ticker = (tickerOverride || tickerInput).trim().toUpperCase();
    if (!ticker) return;
    
    setAnalyzing(true);
    setError("");
    setAnalysisResult(null);
    
    try {
      const response = await fetch(`https://signaliq-api.onrender.com/api/prices/${ticker}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (data.error) throw new Error(data.error);
      setAnalysisResult(data);
      setSelectedTicker(ticker);
      if (data.price_history && data.price_history.length > 0) {
        console.log(`📈 Price history for ${ticker}:`, data.price_history.length, 'points');
        setPriceHistory(data.price_history);
      } else {
        console.warn(`⚠️ No price history for ${ticker}`);
      }
    } catch (err) {
      console.error('Error analyzing ticker:', err);
      setError(`⚠️ Could not fetch data for ${ticker}.`);
    } finally {
      setAnalyzing(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: "24px 32px", display: "flex", justifyContent: "center", alignItems: "center", height: "60vh" }}>
        <div style={{ textAlign: "center", color: C.muted }}>
          <div style={{ fontSize: 24, marginBottom: 16 }}>📊</div>
          <div>Loading market data...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: "24px 32px" }}>
      {/* ============================================ */}
      {/* HEADER */}
      {/* ============================================ */}
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0, letterSpacing: "-0.5px" }}>
          📊 Live Signals
        </h1>
        <p style={{ fontSize: 12, color: C.muted, margin: "4px 0 0" }}>
          NDI = Normalized Sentiment − Normalized Momentum {signals.length > 0 && `• ${signals.length} tickers loaded`}
        </p>
      </div>

      {/* ============================================ */}
      {/* KPIs */}
      {/* ============================================ */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 24 }}>
        <KPI icon="📊" label="Avg NDI" value={avgNDI.toFixed(3)} badge="LIVE" positive={true} />
        <KPI icon="📈" label="Active Signals" value={activeSignals} badge={`${signals.length} total`} positive={true} />
        <KPI icon="🔴" label="Overheating" value={overheating} positive={false} />
        <KPI icon="🎯" label="Avg Confidence" value={`${avgConfidence}%`} badge="REAL" positive={true} />
      </div>

      {/* Error */}
      {error && (
        <div style={{ background: C.redBg, borderRadius: 8, padding: "12px", marginBottom: 16 }}>
          <p style={{ fontSize: 12, color: C.red, margin: 0 }}>{error}</p>
        </div>
      )}

      {/* ============================================ */}
      {/* 1️⃣ 🔍 ANALYZE ANY TICKER */}
      {/* ============================================ */}
      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px", marginBottom: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>🔍 Analyze Any Ticker</h3>
        <div style={{ display: "flex", gap: 12 }}>
          <input
            type="text"
            value={tickerInput}
            onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && analyzeTicker()}
            placeholder="Ex: NVDA, AAPL, MSFT, TSLA"
            style={{
              flex: 1,
              background: C.bg,
              border: `1px solid ${C.cardBorder}`,
              borderRadius: 8,
              padding: "10px 14px",
              color: C.text,
              fontSize: 13,
              outline: "none",
            }}
          />
          <button
            onClick={() => analyzeTicker()}
            disabled={analyzing}
            style={{
              background: C.accent,
              border: "none",
              borderRadius: 8,
              padding: "10px 24px",
              color: "#fff",
              fontWeight: 600,
              fontSize: 13,
              cursor: analyzing ? "not-allowed" : "pointer",
              opacity: analyzing ? 0.6 : 1,
            }}
          >
            {analyzing ? "Analyzing..." : "Analyze →"}
          </button>
        </div>

        {analysisResult && (
          <div style={{ 
            marginTop: 16, 
            background: C.bg, 
            borderRadius: 8, 
            padding: "16px",
            border: `1px solid ${C.cardBorder}`,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 18, fontWeight: 700 }}>{analysisResult.ticker}</span>
              <span style={{
                fontSize: 12,
                background: analysisResult.regime === "Overheating" ? C.redBg :
                           analysisResult.regime === "Watching" ? C.yellowBg : C.greenBg,
                color: analysisResult.regime === "Overheating" ? C.red :
                       analysisResult.regime === "Watching" ? C.yellow : C.green,
                padding: "4px 12px",
                borderRadius: 20,
                fontWeight: 600,
              }}>
                {analysisResult.regime}
              </span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginTop: 12 }}>
              <div><span style={{ fontSize: 10, color: C.muted }}>NDI</span><div style={{ fontSize: 16, fontWeight: 600 }}>+{analysisResult.ndi.toFixed(3)}</div></div>
              <div><span style={{ fontSize: 10, color: C.muted }}>Sentiment</span><div style={{ fontSize: 16, fontWeight: 600 }}>{(analysisResult.sentiment || 0).toFixed(3)}</div></div>
              <div><span style={{ fontSize: 10, color: C.muted }}>Momentum</span><div style={{ fontSize: 16, fontWeight: 600 }}>{(analysisResult.momentum || 0).toFixed(2)}%</div></div>
              <div><span style={{ fontSize: 10, color: C.muted }}>Price</span><div style={{ fontSize: 16, fontWeight: 600 }}>${(analysisResult.current_price || 0).toFixed(2)}</div></div>
            </div>
            <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${C.cardBorder}` }}>
              <p style={{ fontSize: 12, color: C.muted, marginBottom: 4 }}>🤖 SignalIQ Analysis</p>
              <p style={{ fontSize: 13, lineHeight: 1.5 }}>{analysisResult.recommendation}</p>
              <p style={{ fontSize: 11, color: C.accent, marginTop: 8 }}>Confidence: {analysisResult.confidence || 70}%</p>
            </div>
          </div>
        )}
      </div>

      {/* ============================================ */}
      {/* 2️⃣ 📈 PRICE EVOLUTION */}
      {/* ============================================ */}
      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px", marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, margin: 0 }}>
            📈 Price Evolution {selectedTicker ? `(${selectedTicker})` : ''}
          </h3>
          {selectedTicker && (
            <button 
              onClick={() => {
                setPriceHistory([]);
                setTimeout(() => analyzeTicker(selectedTicker), 100);
              }}
              style={{ 
                fontSize: 11, 
                color: C.accent, 
                background: 'transparent', 
                border: '1px solid ' + C.cardBorder,
                borderRadius: 4,
                padding: '4px 12px',
                cursor: 'pointer'
              }}
            >
              ↻ Refresh
            </button>
          )}
        </div>
        {priceHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={priceHistory}>
              <defs>
                <linearGradient id="gPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.accent} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.accent} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: C.muted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: C.muted, fontSize: 10 }} axisLine={false} tickLine={false} domain={['auto', 'auto']} />
              <Tooltip contentStyle={{ background: C.sidebar, border: `1px solid ${C.cardBorder}`, borderRadius: 8 }} />
              <Area type="monotone" dataKey="close" name="Price" stroke={C.accent} strokeWidth={2} fill="url(#gPrice)" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: "center", padding: "40px 0", color: C.muted }}>
            <p>Click a ticker to see its price history</p>
          </div>
        )}
      </div>

      {/* ============================================ */}
      {/* 3️⃣ 📊 SECTOR PERFORMANCE */}
      {/* ============================================ */}
      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px", marginBottom: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>📊 Sector Performance (Avg NDI)</h3>
        {sectorPerformance.map((s) => (
          <div key={s.sector} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
            <span style={{ width: 120, fontSize: 12, color: C.muted }}>{s.sector}</span>
            <div style={{ flex: 1, height: 6, background: C.bg, borderRadius: 4, overflow: "hidden" }}>
              <div style={{
                width: `${Math.min((s.avgNDI + 1) / 2.5 * 100, 100)}%`,
                height: "100%",
                background: s.color,
                borderRadius: 4,
                transition: "width 0.6s ease",
              }} />
            </div>
            <span style={{ width: 40, fontSize: 12, color: C.text, textAlign: "right" }}>
              {s.avgNDI.toFixed(2)}
            </span>
          </div>
        ))}
      </div>

      {/* ============================================ */}
      {/* 4️⃣ 📊 ALL TICKERS (Grid al FINAL) */}
      {/* ============================================ */}
      <div style={{ marginTop: 24 }}>
        <div style={{ display: "flex", gap: 10, marginBottom: 16, flexWrap: "wrap" }}>
          {sectors.map((sector) => (
            <button
              key={sector}
              onClick={() => setSelectedSector(sector)}
              style={{
                background: selectedSector === sector ? C.accent : "transparent",
                color: selectedSector === sector ? "#fff" : C.muted,
                border: `1px solid ${selectedSector === sector ? C.accent : C.cardBorder}`,
                borderRadius: 20,
                padding: "6px 16px",
                fontSize: 12,
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              {sector === "All" ? "📊 All" : sector}
            </button>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14 }}>
          {filteredSignals.map((s) => {
            const regimeKey = getRegimeFromNdi(s.ndi);
            const label = getRegimeLabel(s.ndi);
            const icon = getRegimeIcon(s.ndi);
            const color = getRegimeColor(s.ndi);
            const bg = getRegimeBg(s.ndi);
            
            return (
              <div 
                key={s.ticker} 
                style={{ 
                  background: C.card, 
                  border: `1px solid ${C.cardBorder}`, 
                  borderRadius: 12, 
                  padding: "16px 20px",
                  cursor: "pointer",
                  transition: "all 0.2s",
                  position: "relative",
                  overflow: "hidden",
                }}
                onClick={() => {
                  setTickerInput(s.ticker);
                  analyzeTicker(s.ticker);
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 18, fontWeight: 700 }}>{s.ticker}</span>
                  <span style={{ fontSize: 10, color: C.muted }}>{s.sector}</span>
                </div>
                <div style={{ fontSize: 28, fontWeight: 700, margin: "4px 0", color: color }}>
                  {s.ndi > 0 ? `+${s.ndi.toFixed(3)}` : s.ndi.toFixed(3)}
                </div>
                <div style={{ 
                  fontSize: 11, 
                  background: bg, 
                  color: color, 
                  padding: "2px 12px", 
                  borderRadius: 20, 
                  display: "inline-block",
                  fontWeight: 600,
                }}>
                  {icon} {label}
                </div>
                <div style={{ fontSize: 11, color: C.muted, marginTop: 6 }}>
                  ${s.price || 'N/A'}
                </div>
                <div style={{ 
                  position: "absolute", 
                  bottom: 0, 
                  left: 0, 
                  right: 0, 
                  height: 2, 
                  background: color,
                  opacity: 0.3,
                }} />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
