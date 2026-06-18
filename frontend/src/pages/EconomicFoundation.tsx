import React from 'react';
import { C } from '../components/styles';

export default function EconomicFoundation() {
  return (
    <div style={{ padding: '24px 32px', maxWidth: 1000, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <h1 style={{ fontSize: 28, fontWeight: 700, margin: 0, color: C.text }}>
          📚 Economic Foundation
        </h1>
        <p style={{ fontSize: 14, color: C.muted, margin: '4px 0 0' }}>
          From economics to statistics: the meaning of NDI
        </p>
      </div>

      {/* ===== SECTION 1: WHAT IS NDI ===== */}
      <div style={{ background: C.card, borderRadius: 12, padding: 24, marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 12 }}>📊 What is NDI?</h2>
        <p style={{ fontSize: 14, color: C.text, lineHeight: 1.7, marginBottom: 12 }}>
          The <strong>NDI (Normalized Discrepancy Index)</strong> is a quantitative indicator that measures the <strong>disconnect between market sentiment and price momentum</strong>.
        </p>
        <p style={{ fontSize: 14, color: C.muted, lineHeight: 1.7, fontStyle: 'italic' }}>
          "It doesn't measure whether prices go up or down. It measures whether market confidence and price action are aligned."
        </p>
      </div>

      {/* ===== SECTION 2: ECONOMIC MEANING ===== */}
      <div style={{ background: C.card, borderRadius: 12, padding: 24, marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 12 }}>📐 The Economic Meaning</h2>
        <p style={{ fontSize: 14, color: C.text, lineHeight: 1.7, marginBottom: 12 }}>
          <strong>NDI measures the misalignment between what the market "believes" (sentiment) and what the market "does" (price).</strong>
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div style={{ background: C.bg, borderRadius: 8, padding: 16, textAlign: 'center' }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>🧠</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>Sentiment</div>
            <div style={{ fontSize: 11, color: C.muted }}>Investor confidence</div>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: 16, textAlign: 'center' }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>📈</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>Momentum</div>
            <div style={{ fontSize: 11, color: C.muted }}>Price velocity</div>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: 16, textAlign: 'center', border: `2px solid ${C.accent}` }}>
            <div style={{ fontSize: 24, marginBottom: 4 }}>⚖️</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: C.accent }}>NDI</div>
            <div style={{ fontSize: 11, color: C.muted }}>Discrepancy</div>
          </div>
        </div>

        <div style={{ background: C.bg, borderRadius: 8, padding: 16 }}>
          <p style={{ fontSize: 13, color: C.text, lineHeight: 1.6, margin: 0 }}>
            <strong>NDI = Normalized Sentiment − Normalized Momentum</strong>
          </p>
        </div>
      </div>

      {/* ===== SECTION 3: CAR ANALOGY ===== */}
      <div style={{ background: C.card, borderRadius: 12, padding: 24, marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 12 }}>🚗 The Car Analogy</h2>
        <p style={{ fontSize: 14, color: C.text, lineHeight: 1.7, marginBottom: 12 }}>
          Imagine you're driving a car:
        </p>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12 }}>
          <div style={{ background: C.bg, borderRadius: 8, padding: 16 }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>💭</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>Sentiment</div>
            <div style={{ fontSize: 11, color: C.muted }}>Your desire to accelerate</div>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: 16 }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>🚀</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>Momentum</div>
            <div style={{ fontSize: 11, color: C.muted }}>What the speedometer shows</div>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: 16 }}>
            <div style={{ fontSize: 28, marginBottom: 4 }}>⚠️</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>NDI</div>
            <div style={{ fontSize: 11, color: C.muted }}>The gap between desire and action</div>
          </div>
        </div>
      </div>

      {/* ===== SECTION 4: STATISTICAL MEANING ===== */}
      <div style={{ background: C.card, borderRadius: 12, padding: 24, marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 12 }}>📊 The Statistical Meaning</h2>
        
        <div style={{ background: C.bg, borderRadius: 8, padding: 16, marginBottom: 16 }}>
          <p style={{ fontSize: 13, color: C.text, lineHeight: 1.6, marginBottom: 0 }}>
            <strong>NDI = Z_sentiment − Z_momentum</strong>
          </p>
        </div>

        <p style={{ fontSize: 14, color: C.text, lineHeight: 1.7, marginBottom: 12 }}>
          <strong>Z-score</strong>: measures how many standard deviations a value is from its mean.
        </p>

        <div style={{ background: C.bg, borderRadius: 8, padding: 16 }}>
          <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.6, margin: 0, fontFamily: 'monospace' }}>
            Z = (Value - Mean) / Standard Deviation
          </p>
        </div>
      </div>

      {/* ===== SECTION 5: THE CONNECTION ===== */}
      <div style={{ background: C.card, borderRadius: 12, padding: 24, marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 12 }}>🔗 The Connection: Economics → Statistics → Action</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 12, marginBottom: 16 }}>
          <div style={{ background: C.bg, borderRadius: 8, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 20, marginBottom: 4 }}>📊</div>
            <div style={{ fontSize: 12, color: C.text }}>Economics</div>
            <div style={{ fontSize: 10, color: C.muted }}>Market interpretation</div>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: 12, textAlign: 'center', border: `1px solid ${C.accent}` }}>
            <div style={{ fontSize: 20, marginBottom: 4 }}>📐</div>
            <div style={{ fontSize: 12, color: C.text }}>Statistics</div>
            <div style={{ fontSize: 10, color: C.muted }}>NDI calculation</div>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: 12, textAlign: 'center' }}>
            <div style={{ fontSize: 20, marginBottom: 4 }}>🎯</div>
            <div style={{ fontSize: 12, color: C.text }}>Action</div>
            <div style={{ fontSize: 10, color: C.muted }}>Investment decision</div>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: C.bg }}>
                <th style={{ padding: '8px 12px', textAlign: 'left', color: C.text, borderBottom: `1px solid ${C.cardBorder}` }}>Economics</th>
                <th style={{ padding: '8px 12px', textAlign: 'center', color: C.text, borderBottom: `1px solid ${C.cardBorder}` }}>NDI</th>
                <th style={{ padding: '8px 12px', textAlign: 'left', color: C.text, borderBottom: `1px solid ${C.cardBorder}` }}>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr><td style={{ padding: '6px 12px', color: C.muted, borderBottom: `1px solid ${C.cardBorder}` }}>Euphoric market, price not rising</td><td style={{ padding: '6px 12px', textAlign: 'center', color: '#ef4444', fontWeight: 600, borderBottom: `1px solid ${C.cardBorder}` }}>NDI &gt; 2.0</td><td style={{ padding: '6px 12px', color: '#ef4444', borderBottom: `1px solid ${C.cardBorder}` }}>🔴 SELL</td></tr>
              <tr><td style={{ padding: '6px 12px', color: C.muted, borderBottom: `1px solid ${C.cardBorder}` }}>Strong optimism, momentum weakening</td><td style={{ padding: '6px 12px', textAlign: 'center', color: '#f97316', fontWeight: 600, borderBottom: `1px solid ${C.cardBorder}` }}>1.5 &lt; NDI ≤ 2.0</td><td style={{ padding: '6px 12px', color: '#f97316', borderBottom: `1px solid ${C.cardBorder}` }}>🟠 REDUCE</td></tr>
              <tr><td style={{ padding: '6px 12px', color: C.muted, borderBottom: `1px solid ${C.cardBorder}` }}>Moderate divergence</td><td style={{ padding: '6px 12px', textAlign: 'center', color: '#eab308', fontWeight: 600, borderBottom: `1px solid ${C.cardBorder}` }}>0.5 &lt; NDI ≤ 1.5</td><td style={{ padding: '6px 12px', color: '#eab308', borderBottom: `1px solid ${C.cardBorder}` }}>🟡 MONITOR</td></tr>
              <tr><td style={{ padding: '6px 12px', color: C.muted, borderBottom: `1px solid ${C.cardBorder}` }}>Perfect equilibrium</td><td style={{ padding: '6px 12px', textAlign: 'center', color: '#22c55e', fontWeight: 600, borderBottom: `1px solid ${C.cardBorder}` }}>-0.5 &lt; NDI ≤ 0.5</td><td style={{ padding: '6px 12px', color: '#22c55e', borderBottom: `1px solid ${C.cardBorder}` }}>🟢 HOLD</td></tr>
              <tr><td style={{ padding: '6px 12px', color: C.muted, borderBottom: `1px solid ${C.cardBorder}` }}>Unjustified pessimism</td><td style={{ padding: '6px 12px', textAlign: 'center', color: '#3b82f6', fontWeight: 600, borderBottom: `1px solid ${C.cardBorder}` }}>-1.5 &lt; NDI ≤ -0.5</td><td style={{ padding: '6px 12px', color: '#3b82f6', borderBottom: `1px solid ${C.cardBorder}` }}>🔵 BUY</td></tr>
              <tr><td style={{ padding: '6px 12px', color: C.muted, borderBottom: `1px solid ${C.cardBorder}` }}>Significant oversold</td><td style={{ padding: '6px 12px', textAlign: 'center', color: '#1d4ed8', fontWeight: 600, borderBottom: `1px solid ${C.cardBorder}` }}>-2.0 &lt; NDI ≤ -1.5</td><td style={{ padding: '6px 12px', color: '#1d4ed8', borderBottom: `1px solid ${C.cardBorder}` }}>🔵 STRONG BUY</td></tr>
              <tr><td style={{ padding: '6px 12px', color: C.muted }}>Capitulation</td><td style={{ padding: '6px 12px', textAlign: 'center', color: '#1e3a8a', fontWeight: 600 }}>NDI ≤ -2.0</td><td style={{ padding: '6px 12px', color: '#1e3a8a' }}>🔵 ACCUMULATE</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* ===== SECTION 6: LIVE EXAMPLE ===== */}
      <div style={{ background: C.card, borderRadius: 12, padding: 24, marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 12 }}>📈 Live Example: NVDA</h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
          <div style={{ background: C.bg, borderRadius: 8, padding: 16 }}>
            <div style={{ fontSize: 11, color: C.muted }}>NDI</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#eab308' }}>+0.562</div>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: 16 }}>
            <div style={{ fontSize: 11, color: C.muted }}>Regime</div>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#eab308' }}>🟡 WATCHING</div>
          </div>
        </div>

        <div style={{ background: C.bg, borderRadius: 8, padding: 16 }}>
          <p style={{ fontSize: 13, color: C.text, lineHeight: 1.6, margin: 0 }}>
            <strong>Interpretation:</strong> Sentiment (0.537) is optimistic, but momentum (0.22%) is barely moving. 
            The market is in a <strong>transition phase</strong> where the next direction could be defined. 
            Medium risk - recommended to <strong>monitor closely</strong>.
          </p>
        </div>
      </div>

      {/* ===== SECTION 7: CONCLUSION ===== */}
      <div style={{ background: C.card, borderRadius: 12, padding: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, color: C.text, marginBottom: 12 }}>🎯 Conclusion</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>Buy or sell?</div>
            <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.5, margin: 0 }}>NDI tells you if the market is undervalued or overvalued.</p>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>When to enter?</div>
            <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.5, margin: 0 }}>NDI tells you when pessimism is excessive (buy opportunity).</p>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>When to exit?</div>
            <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.5, margin: 0 }}>NDI tells you when optimism is excessive (sell signal).</p>
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: C.text, marginBottom: 4 }}>What risk?</div>
            <p style={{ fontSize: 13, color: C.muted, lineHeight: 1.5, margin: 0 }}>NDI tells you the magnitude of the imbalance.</p>
          </div>
        </div>
        <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${C.cardBorder}` }}>
          <p style={{ fontSize: 14, color: C.text, lineHeight: 1.7, textAlign: 'center', fontStyle: 'italic' }}>
            "NDI converts market intuition into a quantifiable metric,<br />
            removing emotional bias from financial decisions."
          </p>
        </div>
      </div>
    </div>
  );
}
