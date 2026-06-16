import { C } from "./styles";

export default function Architecture() {
  return (
    <div style={{ padding: "24px 32px", maxWidth: 1200 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>🏗️ System Architecture</h1>
      
      <div style={{ 
        background: C.card, 
        borderRadius: 12, 
        padding: "24px",
        border: `1px solid ${C.cardBorder}`,
        fontFamily: "monospace",
        fontSize: 13,
        lineHeight: 1.8,
        overflowX: "auto",
        marginBottom: 24,
      }}>
        <pre style={{ margin: 0, color: C.text }}>
{`┌───────────────────────────────┐
│    Frontend (React + TS)      │
│    Tailwind + Recharts        │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│       Flask API / Backend     │
│    (Gunicorn + Flask-Limiter) │
└───────────────┬───────────────┘
                │
        ┌───────┴────────┐
        │                │
┌───────▼──────┐  ┌──────▼──────┐
│   NDI Engine │  │  LLM Router │
│  (Layer 4)   │  │  (Multi-LLM)│
└───────┬──────┘  └──────┬──────┘
        │                │
        │        ┌───────┴───────┐
        │        │ Gemini │ Groq │
        │        │        GLM    │
        │        └───────┬───────┘
        │                │
┌───────▼────────────────▼───────┐
│    NLP + Entity Resolution     │
│   Sentiment (Loughran-McDonald)│
│   Momentum (20-day z-score)    │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│      PostgreSQL (Neon)        │
│   10 tables, 13 functions     │
│   6 triggers, pgcrypto        │
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────┐
│    Data Ingestion Layer       │
│  Yahoo Finance (prices)       │
│  6 RSS feeds (news)           │
└───────────────────────────────┘`}
        </pre>
      </div>

      {/* Technology Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16, marginBottom: 24 }}>
        <div style={{ background: C.card, borderRadius: 12, padding: "20px", border: `1px solid ${C.cardBorder}` }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>📊</div>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4, color: C.text }}>Frontend</h3>
          <p style={{ fontSize: 12, color: C.muted, margin: 0 }}>React + TypeScript + Recharts</p>
          <p style={{ fontSize: 11, color: C.dim, margin: 0 }}>Deployed on Vercel</p>
        </div>
        <div style={{ background: C.card, borderRadius: 12, padding: "20px", border: `1px solid ${C.cardBorder}` }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>⚡</div>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4, color: C.text }}>Backend</h3>
          <p style={{ fontSize: 12, color: C.muted, margin: 0 }}>Flask + Python 3.12</p>
          <p style={{ fontSize: 11, color: C.dim, margin: 0 }}>Deployed on Render</p>
        </div>
        <div style={{ background: C.card, borderRadius: 12, padding: "20px", border: `1px solid ${C.cardBorder}` }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>🧠</div>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 4, color: C.text }}>LLM Router</h3>
          <p style={{ fontSize: 12, color: C.muted, margin: 0 }}>Gemini → Groq → GLM</p>
          <p style={{ fontSize: 11, color: C.dim, margin: 0 }}>Graceful fallback</p>
        </div>
      </div>

      {/* Key Principles */}
      <div style={{ 
        background: C.accentBg, 
        borderRadius: 12, 
        padding: "16px 24px",
        border: `1px solid ${C.accent}`,
      }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.accent }}>📐 Key Principles</h3>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px", fontSize: 12, color: C.muted }}>
          <div>✅ Each layer is independent, testable, replaceable</div>
          <div>✅ Data flows unidirectionally (top → bottom)</div>
          <div>✅ Graceful degradation at every step</div>
          <div>✅ Multi-provider LLM fallback chain ensures reliability</div>
        </div>
      </div>
    </div>
  );
}