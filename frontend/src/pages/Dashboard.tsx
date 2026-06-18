import React, { useState, useEffect } from "react";
import { C } from "../components/styles";
import ScanTable from "../components/ScanTable";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { getRegimeInfo } from "../utils/regimeHelpers";

export default function Dashboard() {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [tickerInput, setTickerInput] = useState("");
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [priceHistory, setPriceHistory] = useState<any[]>([]);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        setLoading(true);
        setError("");
        const response = await fetch(
          `https://signaliq-api.onrender.com/api/signals-live`
        );
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        
        if (data.success && data.signals && data.signals.length > 0) {
          const sectorMap: Record<string, string> = {
            'NVDA': 'Technology', 'AAPL': 'Technology', 'MSFT': 'Technology',
            'GOOGL': 'Technology', 'META': 'Technology', 'AMD': 'Technology',
            'AMZN': 'Technology', 'TSLA': 'Automotive', 'JPM': 'Financial', 'KO': 'Consumer'
          };
          const formatted = data.signals.map((item: any) => ({
            ticker: item.ticker,
            ndi: item.ndi || 0,
            regime: item.regime || 'Watching',
            sector: sectorMap[item.ticker] || 'Other',
            price: item.current_price || 'N/A',
            confidence: item.confidence || 70,
          }));
          setSignals(formatted);
        } else {
          setError("No data available from the API.");
          setSignals([]);
        }
      } catch (err) {
        console.error('Error fetching signals:', err);
        setError('⚠️ Could not load market data.');
        setSignals([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSignals();
  }, []);

  const analyzeTicker = async () => {
    const ticker = tickerInput.trim().toUpperCase();
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
      if (data.price_history && data.price_history.length > 0) {
        setPriceHistory(data.price_history);
      }
    } catch (err) {
      console.error('Error analyzing ticker:', err);
      setError(`⚠️ Could not fetch data for ${ticker}.`);
    } finally {
      setAnalyzing(false);
    }
  };

  const avgNDI = signals.length > 0 
    ? signals.reduce((sum, s) => sum + s.ndi, 0) / signals.length 
    : 0;
  const activeSignals = signals.filter(s => s.ndi > 0.7 || s.ndi < -0.7).length;
  const overheating = signals.filter(s => s.ndi > 1.5).length;
  const avgConfidence = signals.length > 0 
    ? Math.round(signals.reduce((sum, s) => sum + (s.confidence || 70), 0) / signals.length) 
    : 0;

  const KPI = ({ icon, label, value, badge }: any) => (
    <div style={{
      background: C.card,
      border: `1px solid ${C.cardBorder}`,
      borderRadius: 12,
      padding: isMobile ? "14px 16px" : "18px 24px",
      minHeight: isMobile ? "80px" : "100px",
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span style={{ fontSize: isMobile ? 13 : 15, color: C.muted }}>{icon} {label}</span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginTop: 4 }}>
        <span style={{ fontSize: isMobile ? 26 : 32, fontWeight: 700, color: C.text }}>{value}</span>
        {badge && (
          <span style={{
            fontSize: 11,
            fontWeight: 700,
            padding: "2px 10px",
            borderRadius: 20,
            background: C.greenBg,
            color: C.green,
          }}>
            {badge}
          </span>
        )}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div style={{ padding: "24px 32px", display: "flex", justifyContent: "center", alignItems: "center", height: "60vh" }}>
        <div style={{ textAlign: "center", color: C.muted }}>
          <div style={{ fontSize: 32, marginBottom: 16 }}>📊</div>
          <div style={{ fontSize: 18 }}>Loading market data...</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: isMobile ? "12px 14px" : "24px 32px", maxWidth: "100vw", overflowX: "hidden" }}>
      
      <div style={{ marginBottom: isMobile ? 16 : 24 }}>
        <h1 style={{ fontSize: isMobile ? 24 : 30, fontWeight: 700, margin: 0, letterSpacing: "-0.5px" }}>
          📊 Live Signals
        </h1>
        <p style={{ fontSize: isMobile ? 13 : 16, color: C.muted, margin: "6px 0 0" }}>
          NDI = Normalized Sentiment − Normalized Momentum • {signals.length} tickers loaded
        </p>
      </div>

      <div style={{ 
        display: "grid", 
        gridTemplateColumns: isMobile ? "1fr 1fr" : "repeat(4,1fr)", 
        gap: isMobile ? 10 : 16, 
        marginBottom: isMobile ? 16 : 24 
      }}>
        <KPI icon="📊" label="Avg NDI" value={avgNDI.toFixed(3)} badge="LIVE" />
        <KPI icon="📈" label="Active" value={activeSignals} badge={`${signals.length} total`} />
        <KPI icon="🔴" label="Overheat" value={overheating} />
        <KPI icon="🎯" label="Confidence" value={`${avgConfidence}%`} badge="REAL" />
      </div>

      {/* Analyze Any Ticker */}
      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: isMobile ? "16px 18px" : "24px 28px", marginBottom: isMobile ? 16 : 24 }}>
        <h3 style={{ fontSize: isMobile ? 16 : 19, fontWeight: 600, marginBottom: isMobile ? 10 : 14 }}>
          🔍 Analyze Any Ticker
        </h3>
        <div style={{ display: "flex", gap: isMobile ? 8 : 14, flexWrap: isMobile ? "wrap" : "nowrap" }}>
          <input
            type="text"
            value={tickerInput}
            onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && analyzeTicker()}
            placeholder="Ex: NVDA, AAPL, MSFT, TSLA"
            style={{
              flex: 1,
              minWidth: isMobile ? "100%" : "auto",
              background: C.bg,
              border: `1px solid ${C.cardBorder}`,
              borderRadius: 8,
              padding: isMobile ? "10px 14px" : "12px 18px",
              color: C.text,
              fontSize: isMobile ? 15 : 17,
              outline: "none",
            }}
          />
          <button
            onClick={analyzeTicker}
            disabled={analyzing}
            style={{
              background: C.accent,
              border: "none",
              borderRadius: 8,
              padding: isMobile ? "10px 20px" : "12px 28px",
              color: "#fff",
              fontWeight: 600,
              fontSize: isMobile ? 15 : 17,
              cursor: analyzing ? "not-allowed" : "pointer",
              opacity: analyzing ? 0.6 : 1,
              width: isMobile ? "100%" : "auto",
            }}
          >
            {analyzing ? "Analyzing..." : "Analyze →"}
          </button>
        </div>

        {analysisResult && (
          <div style={{ 
            marginTop: isMobile ? 14 : 20, 
            background: C.bg, 
            borderRadius: 8, 
            padding: isMobile ? "14px" : "20px",
            border: `1px solid ${C.cardBorder}`,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 8 }}>
              <span style={{ fontSize: isMobile ? 20 : 26, fontWeight: 700 }}>{analysisResult.ticker}</span>
              <span style={{
                fontSize: isMobile ? 13 : 16,
                background: getRegimeInfo(analysisResult.ndi).bgColor,
                color: getRegimeInfo(analysisResult.ndi).color,
                padding: "4px 14px",
                borderRadius: 24,
                fontWeight: 700,
              }}>
                {getRegimeInfo(analysisResult.ndi).icon} {getRegimeInfo(analysisResult.ndi).label}
              </span>
            </div>
            <div style={{ 
              display: "grid", 
              gridTemplateColumns: isMobile ? "1fr 1fr" : "repeat(4,1fr)", 
              gap: isMobile ? 8 : 14, 
              marginTop: isMobile ? 10 : 14 
            }}>
              <div><span style={{ fontSize: isMobile ? 11 : 13, color: C.muted }}>NDI</span><div style={{ fontSize: isMobile ? 18 : 22, fontWeight: 700 }}>{analysisResult.ndi > 0 ? `+${analysisResult.ndi.toFixed(3)}` : analysisResult.ndi.toFixed(3)}</div></div>
              <div><span style={{ fontSize: isMobile ? 11 : 13, color: C.muted }}>Sentiment</span><div style={{ fontSize: isMobile ? 18 : 22, fontWeight: 700 }}>{(analysisResult.sentiment || 0).toFixed(3)}</div></div>
              <div><span style={{ fontSize: isMobile ? 11 : 13, color: C.muted }}>Momentum</span><div style={{ fontSize: isMobile ? 18 : 22, fontWeight: 700 }}>{(analysisResult.momentum || 0).toFixed(2)}%</div></div>
              <div><span style={{ fontSize: isMobile ? 11 : 13, color: C.muted }}>Price</span><div style={{ fontSize: isMobile ? 18 : 22, fontWeight: 700 }}>${(analysisResult.current_price || 0).toFixed(2)}</div></div>
            </div>
            <div style={{ marginTop: isMobile ? 10 : 14, paddingTop: isMobile ? 10 : 14, borderTop: `1px solid ${C.cardBorder}` }}>
              <p style={{ fontSize: isMobile ? 13 : 15, color: C.muted, marginBottom: 4 }}>🤖 SignalIQ Analysis</p>
              <p style={{ fontSize: isMobile ? 14 : 16, lineHeight: 1.6 }}>{analysisResult.recommendation || 'No analysis available'}</p>
              <p style={{ fontSize: isMobile ? 12 : 14, color: C.accent, marginTop: 6 }}>Confidence: {analysisResult.confidence || 70}%</p>
            </div>
          </div>
        )}
      </div>

      {/* Price Evolution */}
      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: isMobile ? "14px 16px" : "20px 24px", marginBottom: isMobile ? 16 : 24 }}>
        <h3 style={{ fontSize: isMobile ? 15 : 18, fontWeight: 600, marginBottom: isMobile ? 8 : 14 }}>
          📈 Price Evolution {analysisResult?.ticker ? `(${analysisResult.ticker})` : ''}
        </h3>
        {priceHistory.length > 0 ? (
          <div style={{ width: "100%", height: isMobile ? 200 : 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={priceHistory}>
                <defs>
                  <linearGradient id="gPrice" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={C.accent} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={C.accent} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: C.muted, fontSize: isMobile ? 9 : 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: C.muted, fontSize: isMobile ? 9 : 11 }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ background: C.sidebar, border: `1px solid ${C.cardBorder}`, borderRadius: 8 }} />
                <Area type="monotone" dataKey="close" name="Price" stroke={C.accent} strokeWidth={2} fill="url(#gPrice)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <div style={{ textAlign: "center", padding: isMobile ? "30px 0" : "50px 0", color: C.muted }}>
            <p style={{ fontSize: isMobile ? 14 : 17 }}>Write a ticker and click Analyze to see its price history</p>
          </div>
        )}
      </div>

      {/* Market Signals */}
      <h3 style={{ fontSize: isMobile ? 15 : 18, fontWeight: 600, marginBottom: isMobile ? 8 : 14 }}>
        📊 Market Signals
      </h3>
      <ScanTable signals={signals} />
    </div>
  );
}
