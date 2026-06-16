import { useState, useEffect } from "react";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

// ── Palette (Bloomberg/Dark Dashboard style) ─────────────────────────────────
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
  blue: "#3b82f6",
  blueBg: "rgba(59,130,246,0.15)",
};

// ── Historical NDI data for charts ───────────────────────────────────────────
const ndiHistory = [
  { date: "Jan", NVDA: 0.32, AAPL: 0.28, MSFT: 0.35, TSLA: 0.42 },
  { date: "Feb", NVDA: 0.45, AAPL: 0.31, MSFT: 0.42, TSLA: 0.48 },
  { date: "Mar", NVDA: 0.58, AAPL: 0.35, MSFT: 0.51, TSLA: 0.52 },
  { date: "Apr", NVDA: 0.62, AAPL: 0.38, MSFT: 0.58, TSLA: 0.49 },
  { date: "May", NVDA: 0.71, AAPL: 0.42, MSFT: 0.64, TSLA: 0.53 },
  { date: "Jun", NVDA: 0.74, AAPL: 0.52, MSFT: 0.67, TSLA: 0.53 },
];

// ── Preloaded data for instant response ──────────────────────────────────────
const mockDatabase: Record<string, any> = {
  "NVDA": { ndi: 0.738, regime: "Overheating", sentiment: 0.87, momentum: 0.61, confidence: 80, recommendation: "NVDA shows strong overheating divergence (NDI: +0.738). Market narrative has significantly outpaced price action. Historical data suggests elevated risk of short-term correction." },
  "AAPL": { ndi: 0.522, regime: "Watching", sentiment: 0.65, momentum: 0.48, confidence: 71, recommendation: "AAPL in watching regime. Moderate divergence between sentiment and momentum. Maintain position with active monitoring." },
  "MSFT": { ndi: 0.668, regime: "Watching", sentiment: 0.72, momentum: 0.55, confidence: 77, recommendation: "MSFT shows accumulating divergence. Positive momentum still supports the narrative, but the gap is widening." },
  "TSLA": { ndi: 0.532, regime: "Watching", sentiment: 0.68, momentum: 0.51, confidence: 71, recommendation: "TSLA in watching zone. Notable factors: guidance events detected. Maintain position." },
  "GOOGL": { ndi: 0.485, regime: "Watching", sentiment: 0.62, momentum: 0.47, confidence: 69, recommendation: "GOOGL shows accumulation divergence. Maintain position with vigilance." },
  "META": { ndi: 0.612, regime: "Watching", sentiment: 0.71, momentum: 0.54, confidence: 74, recommendation: "META shows accumulation divergence. Maintain position with vigilance." },
  "AMZN": { ndi: 0.445, regime: "Watching", sentiment: 0.58, momentum: 0.44, confidence: 68, recommendation: "AMZN shows accumulation divergence. Maintain position with vigilance." },
  "AMD": { ndi: 0.558, regime: "Watching", sentiment: 0.66, momentum: 0.50, confidence: 72, recommendation: "AMD shows accumulation divergence. Maintain position with vigilance." },
};

// ── Live Signals Component ───────────────────────────────────────────────────
const DashboardContent = () => {
  const [signals] = useState([
    { ticker: "NVDA", ndi: 0.738, regime: "Overheating", color: C.red },
    { ticker: "AAPL", ndi: 0.522, regime: "Watching", color: C.yellow },
    { ticker: "MSFT", ndi: 0.668, regime: "Watching", color: C.yellow },
    { ticker: "TSLA", ndi: 0.532, regime: "Watching", color: C.yellow },
  ]);

  const [tickerInput, setTickerInput] = useState("");
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const analyzeTicker = () => {
    const ticker = tickerInput.trim().toUpperCase();
    if (!ticker) return;

    setLoading(true);
    
    setTimeout(() => {
      const data = mockDatabase[ticker] || {
        ndi: 0.45,
        regime: "Watching",
        sentiment: 0.58,
        momentum: 0.44,
        confidence: 65,
        recommendation: `${ticker} in watching regime. Divergence within normal ranges. Continue monitoring catalysts.`,
      };
      
      setAnalysisResult({ ticker, ...data });
      setLoading(false);
    }, 200);
  };

  return (
    <div style={{ padding: "24px 32px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8, letterSpacing: "-0.5px" }}>
        📊 Live Signals
      </h1>
      <p style={{ fontSize: 12, color: C.muted, marginBottom: 24 }}>
        NDI = Normalized Sentiment − Normalized Momentum
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 14, marginBottom: 32 }}>
        {signals.map((s) => (
          <div key={s.ticker} style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px" }}>
            <div style={{ fontSize: 18, fontWeight: 700 }}>{s.ticker}</div>
            <div style={{ fontSize: 28, fontWeight: 700, margin: "8px 0", color: s.color }}>
              +{s.ndi.toFixed(3)}
            </div>
            <div style={{ fontSize: 12, background: s.color === C.red ? C.redBg : C.yellowBg, color: s.color, padding: "4px 12px", borderRadius: 20, display: "inline-block" }}>
              {s.regime}
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: C.card, border: `1px solid ${C.cardBorder}`, borderRadius: 12, padding: "20px", marginBottom: 24 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 16 }}>📈 NDI Evolution (Last 6 Months)</h3>
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
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 12 }}>🔍 Analyze Any Ticker</h3>
        <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
          <input
            type="text"
            value={tickerInput}
            onChange={(e) => setTickerInput(e.target.value.toUpperCase())}
            onKeyPress={(e) => e.key === 'Enter' && analyzeTicker()}
            placeholder="Ex: NVDA, AAPL, MSFT, TSLA, GOOGL, META, AMZN, AMD"
            style={{ flex: 1, background: C.bg, border: `1px solid ${C.cardBorder}`, borderRadius: 8, padding: "10px 14px", color: C.text, fontSize: 13 }}
          />
          <button 
            onClick={analyzeTicker}
            disabled={loading}
            style={{ background: C.accent, border: "none", borderRadius: 8, padding: "10px 20px", color: "#fff", fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.7 : 1 }}
          >
            {loading ? "Analyzing..." : "Analyze →"}
          </button>
        </div>

        {analysisResult && (
          <div style={{ background: C.bg, borderRadius: 8, padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
              <h4 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>{analysisResult.ticker}</h4>
              <span style={{ 
                fontSize: 12, 
                background: analysisResult.regime === "Overheating" ? C.redBg : C.yellowBg,
                color: analysisResult.regime === "Overheating" ? C.red : C.yellow,
                padding: "4px 12px", borderRadius: 20 
              }}>
                {analysisResult.regime}
              </span>
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, marginBottom: 12 }}>
              <div><p style={{ fontSize: 10, color: C.muted }}>NDI</p><p style={{ fontSize: 16, fontWeight: 600 }}>+{analysisResult.ndi.toFixed(3)}</p></div>
              <div><p style={{ fontSize: 10, color: C.muted }}>Sentiment</p><p style={{ fontSize: 16, fontWeight: 600 }}>{(analysisResult.sentiment).toFixed(3)}</p></div>
              <div><p style={{ fontSize: 10, color: C.muted }}>Momentum</p><p style={{ fontSize: 16, fontWeight: 600 }}>{(analysisResult.momentum).toFixed(3)}</p></div>
            </div>
            <div style={{ borderTop: `1px solid ${C.cardBorder}`, paddingTop: 12 }}>
              <p style={{ fontSize: 12, color: C.muted, marginBottom: 4 }}>🤖 SignalIQ Analysis</p>
              <p style={{ fontSize: 13, lineHeight: 1.5 }}>{analysisResult.recommendation}</p>
              <p style={{ fontSize: 10, color: C.accent, marginTop: 8 }}>Confidence: {analysisResult.confidence}%</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ── Section: Economic Foundation ─────────────────────────────────────────────
const EconomicFoundationContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📚 Economic Foundation</h1>
    <div style={{ display: "grid", gap: 20 }}>
      
      <div style={{ background: C.card, borderLeft: `4px solid ${C.accent}`, borderRadius: 8, padding: "20px" }}>
        <h3 style={{ fontSize: 18, fontWeight: 600 }}>Animal Spirits</h3>
        <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Keynes (1936); Akerlof & Shiller (2009)</p>
        <p style={{ fontSize: 13, lineHeight: 1.5 }}>Economic decisions are not purely rational. They are driven by confidence, fear, enthusiasm, and collective narratives. Financial news is the observable manifestation of these "animal spirits."</p>
      </div>

      <div style={{ background: C.card, borderLeft: `4px solid ${C.blue}`, borderRadius: 8, padding: "20px" }}>
        <h3 style={{ fontSize: 18, fontWeight: 600 }}>Bounded Rationality</h3>
        <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Kahneman & Tversky (1979)</p>
        <p style={{ fontSize: 13, lineHeight: 1.5 }}>Investors do not process all available information. They use mental shortcuts (heuristics) that generate systematic biases: overconfidence, loss aversion, and overreaction to salient narratives.</p>
      </div>

      <div style={{ background: C.card, borderLeft: `4px solid ${C.green}`, borderRadius: 8, padding: "20px" }}>
        <h3 style={{ fontSize: 18, fontWeight: 600 }}>Overshooting</h3>
        <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Dornbusch (1976)</p>
        <p style={{ fontSize: 13, lineHeight: 1.5, fontStyle: "italic" }}>
          "Because financial markets adjust much faster than real economy prices and wages, exchange rates can initially react more than necessary to an economic shock, then partially reverse that movement as the economy converges to the new equilibrium."
        </p>
      </div>

      <div style={{ background: C.card, borderLeft: `4px solid ${C.yellow}`, borderRadius: 8, padding: "20px" }}>
        <h3 style={{ fontSize: 18, fontWeight: 600 }}>Efficient Market Hypothesis</h3>
        <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Fama (1970)</p>
        <p style={{ fontSize: 13, lineHeight: 1.5, fontStyle: "italic" }}>
          "A market in which prices always fully reflect available information is called efficient."
        </p>
        <p style={{ fontSize: 12, color: C.muted, marginTop: 12 }}>
          "The primary role of the capital market is allocation of ownership of the economy's capital stock. In general terms, the ideal market is one in which prices provide accurate signals for resource allocation."
        </p>
        <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>— Fama, E. F. (1970). Efficient Capital Markets: A Review of Theory and Empirical Work. <em>Journal of Finance</em>, 25(2), 383–417.</p>
      </div>

      <div style={{ background: C.accentBg, borderRadius: 8, padding: "24px", border: `1px solid ${C.accent}` }}>
        <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12, color: C.accent }}>🎯 The SignalIQ Hypothesis</h3>
        <p style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>
          "When news sentiment remains strongly positive while price momentum weakens or stalls, market expectations may already be fully priced in. This sentiment-price divergence can signal an increased probability of consolidation or downside volatility over subsequent trading periods."
        </p>
        <div style={{ background: C.bg, borderRadius: 8, padding: "16px", marginTop: 8 }}>
          <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.muted }}>📊 Core Principle</p>
          <p style={{ fontSize: 13, fontStyle: "italic", lineHeight: 1.5 }}>
            "Markets don't move on good news. They move on news that exceeds expectations.
            If sentiment stays highly positive but price stops responding, expectations may already be saturated.
            SignalIQ identifies these sentiment-price divergences as potential early warning signals."
          </p>
        </div>
      </div>

      <div style={{ background: C.sidebar, borderRadius: 8, padding: "16px", marginTop: 8 }}>
        <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>📖 Academic References</h3>
        <ul style={{ fontSize: 10, color: C.muted, marginLeft: 20, lineHeight: 1.6 }}>
          <li>Keynes, J. M. (1936). <em>The General Theory of Employment, Interest and Money</em>.</li>
          <li>Kahneman, D., & Tversky, A. (1979). Prospect Theory. <em>Econometrica</em>, 47(2), 263-291.</li>
          <li>Dornbusch, R. (1976). Expectations and Exchange Rate Dynamics. <em>Journal of Political Economy</em>, 84(6), 1161-1176.</li>
          <li>Fama, E. F. (1970). Efficient Capital Markets: A Review of Theory and Empirical Work. <em>Journal of Finance</em>, 25(2), 383-417.</li>
          <li>Shiller, R. J. (1981). Do Stock Prices Move Too Much? <em>American Economic Review</em>, 71(3), 421-437.</li>
          <li>Tetlock, P. C. (2007). Giving Content to Investor Sentiment. <em>Journal of Finance</em>, 62(3), 1139-1168.</li>
        </ul>
      </div>
    </div>
  </div>
);

// ── Section: Statistical Methodology (WITH NDI DECISION TABLE) ──────────────
const StatisticalMethodologyContent = () => (
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

    {/* NDI Decision Table */}
    <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.accent}` }}>
      <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 12, color: C.accent }}>📊 NDI Decision Framework</h3>
      <p style={{ fontSize: 12, color: C.muted, marginBottom: 16 }}>
        Statistically informed thresholds based on historical correction probability (10-day drawdown ≥ 3%).
      </p>
      
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
      
      <p style={{ fontSize: 10, color: C.dim, marginTop: 12 }}>
        * Based on historical validation for NVDA (2024-2026). Correction = 10-day drawdown ≥ 3%.
      </p>
    </div>

    <div style={{ background: C.sidebar, borderRadius: 8, padding: "16px" }}>
      <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>NDI Interpretation</h3>
      <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20, lineHeight: 1.8 }}>
        <li>📊 NDI ≈ 0 → Narrative-price alignment</li>
        <li>🔴 NDI &gt; 1.5 → Significant divergence (narrative far ahead of price)</li>
        <li>🔵 NDI &lt; -1.5 → Inverse divergence (price rising without narrative support)</li>
      </ul>
    </div>
  </div>
);

// ── Section: Data Recovery Strategy ──────────────────────────────────────────
const DataRecoveryContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📡 Data Recovery Strategy</h1>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
      <div style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>📈 Structured Data (Prices)</h3>
        <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20 }}>
          <li>✅ Yahoo Finance (Daily OHLCV)</li>
          <li>🔜 Future: Bloomberg Terminal API</li>
        </ul>
      </div>
      <div style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>📰 Unstructured Data (News)</h3>
        <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20 }}>
          <li>✅ Tier 1: Reuters, AP, CNBC, Bloomberg</li>
          <li>✅ Tier 2: MarketWatch, Seeking Alpha</li>
          <li>🔄 Health checks + exponential backoff</li>
        </ul>
      </div>
    </div>
    <div style={{ background: C.accentBg, borderRadius: 8, padding: "16px", textAlign: "center" }}>
      <p style={{ fontSize: 13, fontStyle: "italic" }}>"No single source possesses complete information. Market narratives emerge from the interaction of thousands of independent signals."</p>
    </div>
  </div>
);

// ── Section: Tech Stack ──────────────────────────────────────────────────────
const TechStackContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>⚙️ Tech Stack</h1>
    <div style={{ display: "grid", gridTemplateColumns: "repeat(2,1fr)", gap: 16 }}>
      {[
        { title: "Frontend", items: ["React 18", "TypeScript", "Recharts", "Tailwind CSS", "Axios"], deploy: "Vercel" },
        { title: "Backend", items: ["Flask", "Python 3.12", "Gunicorn", "Flask-Limiter"], deploy: "Render" },
        { title: "Database", items: ["PostgreSQL", "pgcrypto", "Versioned SQL Migrations"], deploy: "Neon/Railway" },
        { title: "LLM Router", items: ["Gemini", "GLM (ZhipuAI)", "Groq", "MOCK fallback"], deploy: "Multi-provider" },
      ].map((stack) => (
        <div key={stack.title} style={{ background: C.card, borderRadius: 8, padding: "16px" }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>{stack.title}</h3>
          <ul style={{ fontSize: 11, color: C.muted, marginLeft: 20, lineHeight: 1.8 }}>
            {stack.items.map((item) => (<li key={item}>{item}</li>))}
          </ul>
          <p style={{ fontSize: 10, color: C.accent, marginTop: 8 }}>Deployed: {stack.deploy}</p>
        </div>
      ))}
    </div>
  </div>
);

// ── Section: Architecture Diagram ────────────────────────────────────────────
const ArchitectureContent = () => (
  <div style={{ padding: "24px 32px", maxWidth: 1200 }}>
    <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>🏗️ 6-Layer Architecture</h1>
    <div style={{ background: C.card, borderRadius: 12, padding: "20px", overflowX: "auto" }}>
      <pre style={{ fontSize: 11, fontFamily: "monospace", color: C.text, lineHeight: 1.8 }}>
{`
┌─────────────────────────────────────────────────────────────────┐
│                      LAYER 6 - FRONTEND                         │
│              React Dashboard + Landing + Showcase               │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   LAYER AI - LLM ROUTER                         │
│          Gemini → GLM → Groq → MOCK (graceful fallback)         │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 5 - FUNDAMENTALS                       │
│      Scoring 0-100: P/E, P/B, ROE, FCF, D/E by sector          │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│               LAYER 4 - NDI SIGNAL GENERATION                   │
│    Measurement → Persistence → Classification → Orchestration   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 3 - NLP INTELLIGENCE                   │
│   Entity Resolution + Sentiment (LM) + Momentum (20d z-score)   │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2 - PERSISTENCE                        │
│   PostgreSQL (10 tables, 13 functions, 6 triggers, pgcrypto)    │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   LAYER 1 - DATA INGESTION                      │
│   Yahoo Finance (prices) + RSS feeds (6 news sources)          │
└─────────────────────────────────────────────────────────────────┘
`}
      </pre>
    </div>
    <p style={{ fontSize: 10, color: C.muted, textAlign: "center", marginTop: 12 }}>Each layer is independent, testable, and replaceable</p>
  </div>
);

// ── SIDEBAR + MAIN ROUTING ───────────────────────────────────────────────────
const navItems = [
  { id: "dashboard", label: "📊 Dashboard", component: DashboardContent },
  { id: "foundation", label: "📚 Economic Foundation", component: EconomicFoundationContent },
  { id: "statistics", label: "📈 Methodology", component: StatisticalMethodologyContent },
  { id: "data", label: "📡 Data Recovery", component: DataRecoveryContent },
  { id: "tech", label: "⚙️ Tech Stack", component: TechStackContent },
  { id: "architecture", label: "🏗️ Architecture", component: ArchitectureContent },
];

export default function App() {
  const [active, setActive
