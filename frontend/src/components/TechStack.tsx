import { C } from "./styles";

export default function TechStack() {
  return (
    <div style={{ padding: "24px 32px", maxWidth: 1200 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>⚙️ Complete Tech Stack</h1>

      {/* Backend */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>🖥️ Backend (Production)</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
          {[
            { label: "Language", value: "Python 3.12" },
            { label: "Framework", value: "Flask 3.0" },
            { label: "Database", value: "PostgreSQL 16" },
            { label: "ORM", value: "psycopg2-binary" },
            { label: "Deployment", value: "Render (Free)" },
          ].map((item) => (
            <div key={item.label} style={{ background: C.bg, borderRadius: 6, padding: "12px" }}>
              <div style={{ fontSize: 10, color: C.muted }}>{item.label}</div>
              <div style={{ fontSize: 14, color: C.text, fontWeight: 600 }}>{item.value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* APIs & External Services */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>🌐 APIs & External Services</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
          {[
            { label: "Google Gemini", status: "🟢 Active", purpose: "LLM Analysis" },
            { label: "Groq (Llama 70B)", status: "🟢 Ready", purpose: "Alternative LLM" },
            { label: "Yahoo Finance", status: "🟢 Active", purpose: "Stock Prices" },
            { label: "RSS Feeds", status: "🟢 Active", purpose: "News Sources" },
          ].map((item) => (
            <div key={item.label} style={{ background: C.bg, borderRadius: 6, padding: "12px" }}>
              <div style={{ fontSize: 10, color: C.muted }}>{item.purpose}</div>
              <div style={{ fontSize: 14, color: C.text, fontWeight: 600 }}>{item.label}</div>
              <div style={{ fontSize: 11, color: item.status.includes("Active") ? C.green : C.yellow }}>{item.status}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Data Processing */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>📊 Data Processing Libraries</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {["feedparser", "pandas", "numpy", "python-dotenv", "requests", "yfinance"].map((lib) => (
            <span key={lib} style={{ background: C.bg, borderRadius: 20, padding: "4px 14px", fontSize: 12, color: C.text }}>
              {lib}
            </span>
          ))}
        </div>
      </div>

      {/* Database Schema */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>🗄️ Database Schema</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div style={{ background: C.bg, borderRadius: 6, padding: "12px" }}>
            <div style={{ fontSize: 12, color: C.accent, fontWeight: 600, marginBottom: 4 }}>📰 news_articles</div>
            <div style={{ fontSize: 11, color: C.muted }}>id, title, content, source, url UNIQUE, content_hash, created_at</div>
          </div>
          <div style={{ background: C.bg, borderRadius: 6, padding: "12px" }}>
            <div style={{ fontSize: 12, color: C.accent, fontWeight: 600, marginBottom: 4 }}>📈 signal_predictions</div>
            <div style={{ fontSize: 11, color: C.muted }}>id, ticker, score, signal, strength, explanation, price_at_signal, created_at</div>
          </div>
        </div>
      </div>

      {/* Deployment Architecture */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>🚀 Deployment Architecture</h2>
        <pre style={{ fontSize: 11, fontFamily: "monospace", color: C.text, lineHeight: 1.6, background: C.bg, padding: "16px", borderRadius: 8, overflowX: "auto" }}>
{`┌─────────────────────────────────────────────────────┐
│                    RENDER CLOUD                     │
│                                                     │
│  ┌─────────────┐      ┌─────────────────────────┐   │
│  │ PostgreSQL  │◄─────│    Flask API            │   │
│  │  (Render)   │      │      SignalIQ           │   │
│  └─────────────┘      └───────────┬─────────────┘   │
│                                   │                 │
└───────────────────────────────────┼─────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
              ┌──────────┐   ┌──────────┐   ┌──────────┐
              │ yFinance │   │   RSS    │   │  Gemini  │
              │   API    │   │  Feeds   │   │   API    │
              └──────────┘   └──────────┘   └──────────┘`}
        </pre>
      </div>

      {/* Cost Structure */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>💰 Cost Structure</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 12 }}>
          {[
            { label: "Render (Backend)", current: "$0 (Free)", future: "$7-19/mo" },
            { label: "Render (PostgreSQL)", current: "$0 (Free)", future: "$7-19/mo" },
            { label: "Gemini API", current: "$0 (Free tier)", future: "Pay as you go" },
            { label: "Groq API", current: "$0 (Free)", future: "$0 (Free)" },
            { label: "Total Monthly", current: "$0", future: "$14-38/mo" },
          ].map((item) => (
            <div key={item.label} style={{ background: C.bg, borderRadius: 6, padding: "12px" }}>
              <div style={{ fontSize: 10, color: C.muted }}>{item.label}</div>
              <div style={{ fontSize: 13, color: C.green }}>Now: {item.current}</div>
              <div style={{ fontSize: 12, color: C.yellow }}>Soon: {item.future}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Development Environment */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>🛠️ Development Environment</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {["VS Code", "Terminal", "Git", "GitHub", "Python venv", "psql"].map((tool) => (
            <span key={tool} style={{ background: C.bg, borderRadius: 20, padding: "4px 14px", fontSize: 12, color: C.text }}>
              {tool}
            </span>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div style={{ background: C.accentBg, borderRadius: 12, padding: "20px", border: `1px solid ${C.accent}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>📊 Summary</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 12 }}>
          {[
            { label: "Backend", current: "Flask, Python", next: "+ Celery", future: "+ FastAPI" },
            { label: "Database", current: "PostgreSQL", next: "+ Indexes", future: "+ Vector DB" },
            { label: "Frontend", current: "React (Live)", next: "+ Advanced UI", future: "+ Mobile" },
            { label: "AI/LLM", current: "Gemini, Groq", next: "+ Claude", future: "+ Fine-tuned" },
            { label: "Deployment", current: "Render, Vercel", next: "+ GitHub Actions", future: "+ Multi-region" },
          ].map((item) => (
            <div key={item.label} style={{ background: C.bg, borderRadius: 6, padding: "12px" }}>
              <div style={{ fontSize: 10, color: C.muted }}>{item.label}</div>
              <div style={{ fontSize: 12, color: C.green }}>✅ {item.current}</div>
              <div style={{ fontSize: 11, color: C.yellow }}>→ {item.next}</div>
              <div style={{ fontSize: 10, color: C.muted }}>🚀 {item.future}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}