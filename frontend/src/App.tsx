import { useState, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

// ── Paleta (estilo Bloomberg/Dark Dashboard) ─────────────────────────────────
const C = {
  bg: "#0e1117",
  sidebar: "#131720",
  card: "#181f2e",
  cardBorder: "rgba(255,255,255,0.06)",
  text: "#e2e8f0",
  muted: "#6b7280",
  dim: "#374151",
  accent: "#6c63ff",
  accentBg: "rgba(108,99,255,0.15)",
  green: "#10b981",
  greenBg: "rgba(16,185,129,0.15)",
  red: "#ef4444",
  redBg: "rgba(239,68,68,0.15)",
  yellow: "#f59e0b",
  yellowBg: "rgba(245,158,11,0.15)",
  blue: "#3b82f6",           // ✅ AGREGADO
  blueBg: "rgba(59,130,246,0.15)", // ✅ AGREGADO
};

// ── Datos de ejemplo para gráficos (después conectas con API real) ───────────
const ndiHistory = [
  { date: "Ene", NVDA: 0.32, AAPL: 0.28, MSFT: 0.35, TSLA: 0.42 },
  { date: "Feb", NVDA: 0.45, AAPL: 0.31, MSFT: 0.42, TSLA: 0.48 },
  { date: "Mar", NVDA: 0.58, AAPL: 0.35, MSFT: 0.51, TSLA: 0.52 },
  { date: "Abr", NVDA: 0.62, AAPL: 0.38, MSFT: 0.58, TSLA: 0.49 },
  { date: "May", NVDA: 0.71, AAPL: 0.42, MSFT: 0.64, TSLA: 0.53 },
  { date: "Jun", NVDA: 0.74, AAPL: 0.52, MSFT: 0.67, TSLA: 0.53 },
];

// ── Componente de Señales en Vivo ──────────────────────────────────────────
const DashboardContent = () => {
  const [signals] = useState([
    { ticker: "NVDA", ndi: 0.738, regime: "Overheating", color: C.red },
    { ticker: "AAPL", ndi: 0.522, regime: "Watching", color: C.yellow },
    { ticker: "MSFT", ndi: 0.668, regime: "Watching", color: C.yellow },
    { ticker: "TSLA", ndi: 0.532, regime: "Watching", color: C.yellow },
  ]);

  return (
    <div style={{ padding: "24px 32px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, letterSpacing: "-0.5px" }}>
        📊 Señales en Vivo
      </h1>
      <p style={{ fontSize: 12, color: C.muted, marginBottom: 24 }}>
        NDI = Sentimiento Normalizado − Momentum Normalizado
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 32 }}>
        {signals.map((s) => (
          <div key={s.ticker} style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px" }}>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{s.ticker}</div>
            <div style={{ fontSize: 28, fontWeight: 700, margin: "8px 0", color: s.color }}>
              {s.ndi > 0 ? `+${s.ndi.toFixed(3)}` : s.ndi.toFixed(3)}
            </div>
            <div style={{ fontSize: 12, background: s.color === C.red ? C.redBg : C.yellowBg, color: s.color, padding: "4px 12px", borderRadius: 20, display: "inline-block" }}>
              {s.regime}
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px", marginBottom: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>📈 Evolución del NDI (últimos 6 meses)</h3>
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={ndiHistory}>
            <defs>
              <linearGradient id="gNVDA" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={C.red} stopOpacity={0.3} />
                <stop offset="95%" stopColor={C.red} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" vertical={false} />
            <XAxis dataKey="date" tick={{ fill: C.muted, fontSize: 10 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: C.muted, fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip contentStyle={{ background: C.sidebar, border: `1px solid ${C.cardBorder}`, borderRadius: 8 }} />
            <Area type="monotone" dataKey="NVDA" name="NVDA" stroke={C.red} strokeWidth={2} fill="url(#gNVDA)" />
            <Area type="monotone" dataKey="AAPL" name="AAPL" stroke={C.yellow} strokeWidth={2} fill="none" />
            <Area type="monotone" dataKey="MSFT" name="MSFT" stroke={C.green} strokeWidth={2} fill="none" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>🔍 Analizar cualquier ticker</h3>
        <div style={{ display: "flex", gap: 12 }}>
          <input
            type="text"
            placeholder="Ej: NVDA, AAPL, MSFT"
            style={{ flex: 1, background: C.bg, border: `1px solid ${C.cardBorder}`, borderRadius: 8, padding: "10px 14px", color: C.text, fontSize: 13 }}
          />
          <button style={{ background: C.accent, border: "none", borderRadius: 8, padding: "10px 20px", color: "#fff", fontWeight: 600, cursor: "pointer" }}>
            Analizar →
          </button>
        </div>
      </div>
    </div>
  );
};

// ── Sección: Fundamento Económico ──────────────────────────────────────────
const FundamentoContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📚 Fundamento Económico</h1>
    <div style={{ display: "grid", gap: 20 }}>
      {[
        { title: "Animal Spirits", author: "Keynes (1936); Akerlof & Shiller (2009)", text: "Las decisiones económicas no son puramente racionales. Están impulsadas por confianza, miedo, entusiasmo y narrativas colectivas. Las noticias financieras son la manifestación observable de estos 'espíritus animales'.", color: C.accent },
        { title: "Rationalidad Limitada", author: "Kahneman & Tversky (1979)", text: "Los inversores no procesan toda la información disponible. Usan atajos mentales (heurísticos) que generan sesgos sistemáticos: exceso de confianza, aversión a la pérdida, y sobrerreacción a narrativas salientes.", color: C.blue },
        { title: "Overshooting", author: "Dornbusch (1976)", text: "En mercados con ruido y feedback lento, los precios sobre-reaccionan inicialmente y luego corrigen. Cuando el NDI es alto (narrativa muy positiva, precios planos o cayendo), SignalIQ detecta el pico del overshoot.", color: C.green },
      ].map((item) => (
        <div key={item.title} style={{ background: C.card, borderLeft: `4px solid ${item.color}`, borderRadius: 8, padding: "20px" }}>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>{item.title}</h3>
          <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>{item.author}</p>
          <p style={{ fontSize: 13, lineHeight: 1.5 }}>{item.text}</p>
        </div>
      ))}
      <div style={{ background: C.accentBg, borderRadius: 8, padding: "20px", textAlign: "center" }}>
        <p style={{ fontSize: 14, fontStyle: "italic" }}>"Cuando la historia es muy buena pero los precios dejan de subir, la historia está a punto de agotarse."</p>
        <p style={{ fontSize: 11, color: C.muted, marginTop: 8 }}>— Hipótesis Central de SignalIQ</p>
      </div>
    </div>
  </div>
);

// ── Sección: Procedimiento Estadístico ───────────────────────────────────────
const EstadisticaContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📈 Procedimiento Estadístico</h1>
    <div style={{ background: C.card, borderRadius: 12, padding: "24px", textAlign: "center", marginBottom: 24 }}>
      <code style={{ fontSize: 20, fontFamily: "monospace", background: C.bg, padding: "12px 20px", borderRadius: 8, display: "inline-block" }}>
        NDI = Z_sentiment − Z_momentum
      </code>
      <p style={{ fontSize: 11, color: C.muted, marginTop: 12 }}>Z = (X − μ) / σ</p>
    </div>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
      <div style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Sentimiento (S_news)</h3>
        <p style={{ fontSize: 12, color: C.muted }}>Media móvil 5 días del sentimiento de noticias (Léxico Loughran-McDonald)</p>
        <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>μ_s, σ_s: históricos de 252 días</p>
      </div>
      <div style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Momentum (M_price)</h3>
        <p style={{ fontSize: 12, color: C.muted }}>Retorno acumulado 5 días de precios ajustados</p>
        <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>μ_m, σ_m: históricos de 252 días</p>
      </div>
    </div>
    <div style={{ background: C.sidebar, borderRadius: 8, padding: "16px" }}>
      <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Interpretación del NDI</h3>
      <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20, lineHeight: 1.6 }}>
        <li>📊 NDI ≈ 0 → Narrativa y precio alineados</li>
        <li>🔴 NDI &gt; 1.5 → Divergencia significativa (narrativa muy por delante)</li>
        <li>🔵 NDI &lt; -1.5 → Divergencia inversa (precio sube sin narrativa)</li>
      </ul>
    </div>
  </div>
);

// ── Sección: Data Recovery ───────────────────────────────────────────────────
const DataRecoveryContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📡 Estrategia de Adquisición de Datos</h1>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
      <div style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>📈 Precios (Estructurados)</h3>
        <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20 }}>
          <li>✅ Yahoo Finance (OHLCV diario)</li>
          <li>🔜 Futuro: Bloomberg Terminal API</li>
        </ul>
      </div>
      <div style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>📰 Noticias (No estructuradas)</h3>
        <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20 }}>
          <li>✅ Tier 1: Reuters, AP, CNBC, Bloomberg</li>
          <li>✅ Tier 2: MarketWatch, Seeking Alpha</li>
          <li>🔄 Health checks + backoff exponencial</li>
        </ul>
      </div>
    </div>
    <div style={{ background: C.accentBg, borderRadius: 8, padding: "16px", textAlign: "center" }}>
      <p style={{ fontSize: 13, fontStyle: "italic" }}>"Ninguna fuente individual posee información completa. Las narrativas de mercado emergen de la interacción de miles de señales independientes."</p>
    </div>
  </div>
);

// ── Sección: Tech Stack ──────────────────────────────────────────────────────
const TechStackContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>⚙️ Tech Stack</h1>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 16 }}>
      {[
        { title: "Frontend", items: ["React 18", "TypeScript", "Recharts", "Tailwind CSS", "Axios"], deploy: "Vercel" },
        { title: "Backend", items: ["Flask", "Python 3.12", "Gunicorn", "Flask-Limiter"], deploy: "Render" },
        { title: "Base de Datos", items: ["PostgreSQL", "pgcrypto", "Migraciones SQL versionadas"], deploy: "Neon/Railway" },
        { title: "LLM Router", items: ["Gemini", "GLM (ZhipuAI)", "Groq", "MOCK fallback"], deploy: "Multi-provider" },
      ].map((stack) => (
        <div key={stack.title} style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{stack.title}</h3>
          <ul style={{ fontSize: 11, color: C.muted, marginLeft: 20, lineHeight: 1.8 }}>
            {stack.items.map((item) => (<li key={item}>{item}</li>))}
          </ul>
          <p style={{ fontSize: 10, color: C.accent, marginTop: 8 }}>Deploy: {stack.deploy}</p>
        </div>
      ))}
    </div>
  </div>
);

// ── Sección: Diagrama de Arquitectura ────────────────────────────────────────
const ArquitecturaContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1200 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>🏗️ Arquitectura de 6 Capas</h1>
    <div style={{ background: C.card, borderRadius: 12, padding: "20px", overflowX: "auto" }}>
      <pre style={{ fontSize: 11, fontFamily: "monospace", color: C.text, lineHeight: 1.8 }}>
{`
┌─────────────────────────────────────────────────────────────────┐
│                      CAPA 6 - FRONTEND                          │
│         React Dashboard + Landing Page + Showcase               │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA AI - LLM ROUTER                         │
│         Gemini → GLM → Groq → MOCK (fallback graceful)          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA 5 - FUNDAMENTALS                       │
│         Scoring 0-100: P/E, P/B, ROE, FCF, D/E por sector       │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                CAPA 4 - NDI SIGNAL GENERATION                   │
│    Measurement → Persistence → Classification → Orchestration   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA 3 - NLP INTELLIGENCE                   │
│    Entity Resolution + Sentiment (LM) + Momentum (20d z-score)  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     CAPA 2 - PERSISTENCE                        │
│    PostgreSQL (10 tables, 13 functions, 6 triggers, pgcrypto)   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    CAPA 1 - DATA INGESTION                      │
│    Yahoo Finance (precios) + RSS feeds (6 fuentes de noticias)  │
└─────────────────────────────────────────────────────────────────┘
`}
      </pre>
    </div>
    <p style={{ fontSize: 10, color: C.muted, textAlign: "center", marginTop: 12 }}>Cada capa es independiente, testeable y reemplazable</p>
  </div>
);

// ── SIDEBAR + ROUTING PRINCIPAL ─────────────────────────────────────────────
const navItems = [
  { id: "dashboard", label: "📊 Dashboard", component: DashboardContent },
  { id: "fundamento", label: "📚 Fundamento", component: FundamentoContent },
  { id: "estadistica", label: "📈 Estadística", component: EstadisticaContent },
  { id: "data", label: "📡 Data Recovery", component: DataRecoveryContent },
  { id: "tech", label: "⚙️ Tech Stack", component: TechStackContent },
  { id: "arquitectura", label: "🏗️ Arquitectura", component: ArquitecturaContent },
];

export default function App() {
  const [active, setActive] = useState("dashboard");
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const ActiveComponent = navItems.find((item) => item.id === active)?.component || DashboardContent;

  return (
    <div style={{ display: "flex", height: "100vh", background: C.bg, color: C.text, fontFamily: "'Inter', sans-serif", overflow: "hidden" }}>

      {/* Sidebar fija */}
      <div style={{ width: 240, background: C.sidebar, borderRight: `1px solid ${C.cardBorder}`, display: "flex", flexDirection: "column", overflowY: "auto" }}>
        <div style={{ padding: "24px 20px", borderBottom: `1px solid ${C.cardBorder}`, marginBottom: 16 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 32, height: 32, borderRadius: 8, background: "linear-gradient(135deg, #6c63ff, #3b82f6)", display: "flex", alignItems: "center", justifyContent: "center" }}>◈</div>
            <span style={{ fontWeight: 700, fontSize: 16 }}>SignalIQ</span>
          </div>
          <p style={{ fontSize: 10, color: C.muted, marginTop: 8 }}>Intelligence Beyond Narratives</p>
        </div>

        {navItems.map((item) => (
          <div
            key={item.id}
            onClick={() => setActive(item.id)}
            style={{
              padding: "12px 20px",
              margin: "4px 12px",
              borderRadius: 8,
              fontSize: 13,
              cursor: "pointer",
              background: active === item.id ? C.accentBg : "transparent",
              color: active === item.id ? C.text : C.muted,
              borderLeft: active === item.id ? `2px solid ${C.accent}` : "2px solid transparent",
            }}
          >
            {item.label}
          </div>
        ))}

        <div style={{ marginTop: "auto", padding: "20px", borderTop: `1px solid ${C.cardBorder}`, fontSize: 10, color: C.muted, textAlign: "center" }}>
          <div>{time.toLocaleTimeString("en-US", { hour12: false })}</div>
          <div style={{ marginTop: 8 }}>© 2026 SignalIQ</div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, overflow: "auto" }}>
        <ActiveComponent />
      </div>
    </div>
  );
}