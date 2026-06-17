import React, { useState, useEffect } from "react";
import { C } from "./styles";
import ScanTable from "./ScanTable";

export default function Dashboard() {
  const [signals, setSignals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

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
          const formatted = data.signals.map((item: any) => ({
            ticker: item.ticker,
            ndi: item.ndi || 0,
            regime: item.regime || 'Aligned',
            confidence: (item.confidence || 70) / 100,
            price: item.current_price || 0,
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
    const interval = setInterval(fetchSignals, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

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
    <div style={{ padding: "24px 32px", maxWidth: "100vw", overflowX: "hidden" }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: 0, letterSpacing: "-0.5px" }}>
          📊 Live Signals
        </h1>
        <p style={{ fontSize: 12, color: C.muted, margin: "4px 0 0" }}>
          NDI = Normalized Sentiment − Normalized Momentum • {signals.length} tickers loaded
        </p>
      </div>

      {error && (
        <div style={{ background: C.redBg, borderRadius: 8, padding: "10px 14px", marginBottom: 16 }}>
          <p style={{ fontSize: 12, color: C.red, margin: 0 }}>{error}</p>
        </div>
      )}

      <ScanTable signals={signals} />
    </div>
  );
}
