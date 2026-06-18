import React, { useState } from 'react';
import { C } from '../components/styles';
import TickerAnalysis from '../components/TickerAnalysis';

export default function Intelligence() {
  const [ticker, setTicker] = useState('');
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);

  const handleAnalyze = () => {
    if (ticker.trim()) {
      setSelectedTicker(ticker.trim().toUpperCase());
    }
  };

  if (selectedTicker) {
    return <TickerAnalysis ticker={selectedTicker} onBack={() => setSelectedTicker(null)} />;
  }

  return (
    <div style={{ padding: "24px 32px", maxWidth: 800 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>🧠 Intelligence</h1>
      <p style={{ fontSize: 13, color: C.muted, marginBottom: 24 }}>
        Ingresá un ticker para ver el análisis detallado con NDI, gráficos e interpretación.
      </p>

      <div style={{ display: "flex", gap: 12, maxWidth: 500 }}>
        <input
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          onKeyPress={(e) => e.key === 'Enter' && handleAnalyze()}
          placeholder="Ej: NVDA, AAPL, MSFT"
          style={{
            flex: 1,
            padding: "12px 16px",
            borderRadius: 8,
            border: `1px solid ${C.cardBorder}`,
            background: C.bg,
            color: C.text,
            fontSize: 15,
            outline: "none",
          }}
        />
        <button
          onClick={handleAnalyze}
          style={{
            background: C.accent,
            border: "none",
            borderRadius: 8,
            padding: "12px 24px",
            color: "#fff",
            fontWeight: 600,
            fontSize: 15,
            cursor: "pointer",
          }}
        >
          Analizar →
        </button>
      </div>
    </div>
  );
}
