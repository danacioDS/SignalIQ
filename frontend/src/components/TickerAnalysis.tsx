import { useState, useEffect } from "react";
import { C } from "./styles";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

interface TickerAnalysisProps {
  ticker: string;
  onBack: () => void;
}

export default function TickerAnalysis({ ticker, onBack }: TickerAnalysisProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [data, setData] = useState<any>(null);
  const [priceHistory, setPriceHistory] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError("");
        const response = await fetch(`https://signaliq-api.onrender.com/api/prices/${ticker}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const result = await response.json();
        if (result.error) throw new Error(result.error);
        setData(result);
        if (result.price_history && result.price_history.length > 0) {
          const prices = result.price_history.map((item: any) => item.close);
          const min = Math.min(...prices);
          const max = Math.max(...prices);
          const range = max - min;
          const normalized = result.price_history.map((item: any) => ({
            date: item.date,
            ndi: range > 0 ? (item.close - min) / range : 0.5
          }));
          setPriceHistory(normalized);
        }
      } catch (err) {
        console.error('Error fetching ticker data:', err);
        setError(`⚠️ Could not load data for ${ticker}.`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [ticker]);

  // ── Determinar régimen ──────────────────────────────────────────────────────
  const getRegimeInfo = (ndi: number) => {
    if (ndi > 1.5) return { label: "Overheating", color: C.red, bg: C.redBg, icon: "🔴" };
    if (ndi > 0.5) return { label: "Watching", color: C.yellow, bg: C.yellowBg, icon: "🟡" };
    if (ndi > -0.5) return { label: "Aligned", color: C.green, bg: C.greenBg, icon: "🟢" };
    return { label: "Undervalued", color: C.blue, bg: C.blueBg, icon: "🔵" };
  };

  // ── Generar interpretación ──────────────────────────────────────────────────
  const getInterpretation = (ndi: number, sentiment: number, momentum: number) => {
    if (ndi > 1.5) {
      return `El sentimiento (${sentiment.toFixed(2)}) está muy por encima del momentum (${momentum.toFixed(1)}%). Históricamente, niveles similares han precedido correcciones de corto plazo. Se recomienda precaución.`;
    }
    if (ndi > 0.5) {
      return `La narrativa positiva está ganando terreno, pero el precio aún no ha validado completamente las expectativas. El mercado está en un punto de inflexión.`;
    }
    if (ndi > -0.5) {
      return `Narrativa y precio están alineados. No hay señales claras de divergencia. El mercado está en equilibrio.`;
    }
    return `El precio está superando al sentimiento, lo que puede indicar que el mercado está descontando noticias negativas que aún no son ampliamente conocidas.`;
  };

  if (loading) {
    return (
      <div style={{ padding: "24px 32px", display: "flex", justifyContent: "center", alignItems: "center", height: "60vh" }}>
        <div style={{ textAlign: "center", color: C.muted }}>
          <div style={{ fontSize: 24, marginBottom: 16 }}>📊</div>
          <div>Loading analysis for {ticker}...</div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ padding: "24px 32px" }}>
        <button onClick={onBack} style={{
          background: "transparent",
          border: "none",
          color: C.muted,
          cursor: "pointer",
          fontSize: 13,
          padding: "8px 16px",
          marginBottom: 16,
        }}>← Volver</button>
        <div style={{ background: C.redBg, borderRadius: 8, padding: "16px", textAlign: "center" }}>
          <p style={{ color: C.red, margin: 0 }}>{error || "No data available"}</p>
        </div>
      </div>
    );
  }

  const regime = getRegimeInfo(data.ndi);
  const interpretation = getInterpretation(data.ndi, data.sentiment || 0.5, data.momentum || 0);

  return (
    <div style={{ padding: "24px 32px", maxWidth: 1200 }}>
      {/* ── Botón Volver ── */}
      <button onClick={onBack} style={{
        background: "transparent",
        border: "none",
        color: C.muted,
        cursor: "pointer",
        fontSize: 13,
        padding: "8px 16px",
        marginBottom: 16,
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}>
        ← Volver al Dashboard
      </button>

      {/* ── Header ── */}
      <div style={{
        background: C.card,
        border: `1px solid ${C.cardBorder}`,
        borderRadius: 12,
        padding: "24px",
        marginBottom: 24,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0 }}>{ticker}</h1>
          <div style={{ display: "flex", gap: 20, marginTop: 8, fontSize: 13, color: C.muted }}>
            <span>NDI: <strong style={{ color: C.text }}>{data.ndi.toFixed(3)}</strong></span>
            <span>Sentiment: <strong style={{ color: C.text }}>{(data.sentiment || 0).toFixed(3)}</strong></span>
            <span>Price: <strong style={{ color: C.text }}>${(data.current_price || 0).toFixed(2)}</strong></span>
          </div>
        </div>
        <div style={{
          background: regime.bg,
          color: regime.color,
          padding: "8px 20px",
          borderRadius: 20,
          fontSize: 16,
          fontWeight: 600,
        }}>
          {regime.icon} {regime.label}
        </div>
      </div>

      {/* ── Grid de análisis ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
        
        {/* ── Termómetro NDI ── */}
        <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>🎯 NDI Termometer</h3>
          <div style={{ position: "relative", padding: "8px 0" }}>
            <div style={{
              height: 8,
              background: `linear-gradient(to right, #3b82f6, #10b981, #f59e0b, #ef4444)`,
              borderRadius: 4,
              position: "relative",
            }}>
              <div style={{
                position: "absolute",
                top: -6,
                left: `${((data.ndi + 2) / 4) * 100}%`,
                width: 16,
                height: 16,
                background: "white",
                borderRadius: "50%",
                border: `2px solid ${regime.color}`,
                transform: "translateX(-50%)",
                boxShadow: "0 0 12px rgba(0,0,0,0.3)",
              }} />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontSize: 10, color: C.muted }}>
              <span>-2.0</span>
              <span>Undervalued</span>
              <span>Aligned</span>
              <span>Overheating</span>
              <span>+2.0</span>
            </div>
            <div style={{ textAlign: "center", marginTop: 12 }}>
              <span style={{ fontSize: 24, fontWeight: 700, color: regime.color }}>
                {data.ndi.toFixed(3)}
              </span>
              <span style={{ fontSize: 12, color: C.muted, marginLeft: 8 }}>/ 2.0</span>
            </div>
          </div>
        </div>

        {/* ── Interpretación ── */}
        <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>📖 Interpretación</h3>
          <p style={{ fontSize: 13, lineHeight: 1.6, color: C.muted }}>{interpretation}</p>
          <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${C.cardBorder}` }}>
            <p style={{ fontSize: 12, color: C.muted }}>
              Confianza: <strong style={{ color: C.text }}>{data.confidence || 70}%</strong>
            </p>
          </div>
        </div>
      </div>

      {/* ── Comparativa con sector ── */}
      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px", marginBottom: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>📊 Comparativa con el sector</h3>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: C.muted, marginBottom: 4 }}>
              <span>{ticker}</span>
              <span>{data.ndi.toFixed(3)}</span>
            </div>
            <div style={{ height: 8, background: C.bg, borderRadius: 4, overflow: "hidden" }}>
              <div style={{
                width: `${Math.min((data.ndi + 1) / 2.5 * 100, 100)}%`,
                height: "100%",
                background: regime.color,
                borderRadius: 4,
              }} />
            </div>
          </div>
          <div style={{ fontSize: 12, color: C.muted, minWidth: 60, textAlign: "right" }}>
            Sector
          </div>
        </div>
        <p style={{ fontSize: 11, color: C.dim, marginTop: 12 }}>
          {ticker} está {data.ndi > 0.5 ? "por encima" : "en línea con"} del promedio del sector
        </p>
      </div>

      {/* ── Gráfico de evolución ── */}
      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px", marginBottom: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>📈 NDI Evolution</h3>
        {priceHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={priceHistory}>
              <defs>
                <linearGradient id="gNDI" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={C.accent} stopOpacity={0.3} />
                  <stop offset="95%" stopColor={C.accent} stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
              <XAxis dataKey="date" tick={{ fill: C.muted, fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: C.muted, fontSize: 10 }} axisLine={false} tickLine={false} domain={[0, 1]} />
              <Tooltip contentStyle={{ background: C.sidebar, border: `1px solid ${C.cardBorder}`, borderRadius: 8 }} />
              <Area type="monotone" dataKey="ndi" name="NDI" stroke={C.accent} strokeWidth={2} fill="url(#gNDI)" />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div style={{ textAlign: "center", padding: "40px 0", color: C.muted }}>
            <p>No historical data available</p>
          </div>
        )}
      </div>
    </div>
  );
}