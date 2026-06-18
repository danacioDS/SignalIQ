import React from 'react';
import { C } from './styles';

export default function Methodology() {
  return (
    <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📈 Statistical Methodology</h1>
      
      <div style={{ background: C.card, borderRadius: 12, padding: "24px", textAlign: "center", marginBottom: 24 }}>
        <code style={{ fontSize: 20, fontFamily: "monospace", background: C.bg, padding: "12px 20px", borderRadius: 8, display: "inline-block" }}>
          NDI = Z_sentiment − Z_momentum
        </code>
        <p style={{ fontSize: 11, color: C.muted, marginTop: 12 }}>Z = (X − μ) / σ</p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
        <div style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Sentiment (S_news)</h3>
          <p style={{ fontSize: 12, color: C.muted }}>5-day moving average of news sentiment (Loughran-McDonald lexicon)</p>
          <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>μ_s, σ_s: 252-day historical window</p>
        </div>
        <div style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Momentum (M_price)</h3>
          <p style={{ fontSize: 12, color: C.muted }}>5-day cumulative return of adjusted prices</p>
          <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>μ_m, σ_m: 252-day historical window</p>
        </div>
      </div>

      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.accent}` }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: C.accent }}>📊 NDI Decision Framework</h3>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: C.sidebar, color: C.text }}>
                <th style={{ padding: "10px 12px", textAlign: "left", borderBottom: `1px solid ${C.cardBorder}` }}>NDI Range</th>
                <th style={{ padding: "10px 12px", textAlign: "left", borderBottom: `1px solid ${C.cardBorder}` }}>Regime</th>
                <th style={{ padding: "10px 12px", textAlign: "center", borderBottom: `1px solid ${C.cardBorder}` }}>Correction Rate</th>
                <th style={{ padding: "10px 12px", textAlign: "left", borderBottom: `1px solid ${C.cardBorder}` }}>Suggested Action</th>
              </tr>
            </thead>
            <tbody>
              {[
                { range: "NDI ≤ -2.0", regime: "🔵 Extreme Undervalued", rate: "High?", action: "Accumulation Signal" },
                { range: "-2.0 < NDI ≤ -1.5", regime: "🔵 Strong Undervalued", rate: "Medium-High", action: "Monitor" },
                { range: "-1.5 < NDI ≤ -0.5", regime: "🟢 Aligned", rate: "Low", action: "Neutral" },
                { range: "-0.5 < NDI ≤ 0.5", regime: "🟢 Stable", rate: "Very Low", action: "Neutral / Hold" },
                { range: "0.5 < NDI ≤ 1.5", regime: "🟡 Watching", rate: "Medium", action: "Monitor" },
                { range: "1.5 < NDI ≤ 2.0", regime: "🟠 Overheating", rate: "High", action: "Consider reducing" },
                { range: "NDI > 2.0", regime: "🔴 Extreme Overheating", rate: "Very High", action: "Sell Signal" },
              ].map((row, i) => (
                <tr key={i} style={{ borderBottom: i < 6 ? `1px solid ${C.cardBorder}` : 'none' }}>
                  <td style={{ padding: "10px 12px", fontFamily: "monospace", fontSize: 12 }}>{row.range}</td>
                  <td style={{ padding: "10px 12px" }}>{row.regime}</td>
                  <td style={{ padding: "10px 12px", textAlign: "center" }}>{row.rate}</td>
                  <td style={{ padding: "10px 12px" }}>{row.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
