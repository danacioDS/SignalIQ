import { C } from "./styles";

export default function DataRecovery() {
  return (
    <div style={{ padding: "24px 32px", maxWidth: 1200 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📡 Data Acquisition Strategy</h1>
      
      <p style={{ fontSize: 13, color: C.muted, marginBottom: 24, lineHeight: 1.6 }}>
        SignalIQ builds a balanced representation of financial reality by combining structured market data with unstructured narrative data. 
        The system observes not only what markets are doing, but also what influential information sources are saying about markets.
      </p>

      {/* Structured Data */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>📊 Structured Financial Data</h2>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div style={{ background: C.bg, borderRadius: 8, padding: "16px" }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.text }}>Market Prices</h3>
            <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20, lineHeight: 1.8 }}>
              <li>✅ Individual Equities</li>
              <li>✅ Equity Indices</li>
              <li>✅ Commodities</li>
              <li>✅ Currency Pairs</li>
              <li>✅ Government Bonds</li>
              <li>✅ ETFs</li>
            </ul>
            <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>Primary: Yahoo Finance • Daily intervals</p>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: "16px" }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.text }}>Macroeconomic Data</h3>
            <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20, lineHeight: 1.8 }}>
              <li>🌍 USD/CNY, USD/JPY, EUR/USD, GBP/USD</li>
              <li>🏛️ US Treasuries, UK Gilts, JGBs</li>
              <li>🛢️ Crude Oil, Gold, Copper, Lithium</li>
            </ul>
            <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>Purpose: Inflation, Growth, Capital Flows</p>
          </div>
        </div>
      </div>

      {/* Narrative Intelligence Sources */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>📰 Narrative Intelligence Sources</h2>
        
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
          <div style={{ background: C.bg, borderRadius: 8, padding: "16px" }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.text }}>📌 Tier 1 Sources (High Influence)</h3>
            <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20, lineHeight: 1.8 }}>
              <li>✅ Reuters</li>
              <li>✅ Associated Press</li>
              <li>✅ CNBC</li>
              <li>✅ Bloomberg (public)</li>
              <li>✅ Yahoo Finance</li>
            </ul>
          </div>
          <div style={{ background: C.bg, borderRadius: 8, padding: "16px" }}>
            <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.text }}>📌 Tier 2 Sources (Medium Influence)</h3>
            <ul style={{ fontSize: 12, color: C.muted, marginLeft: 20, lineHeight: 1.8 }}>
              <li>✅ MarketWatch</li>
              <li>✅ Seeking Alpha</li>
              <li>✅ The Motley Fool</li>
              <li>✅ Barron's (public)</li>
            </ul>
          </div>
        </div>

        {/* Media Diversification */}
        <div style={{ background: C.bg, borderRadius: 8, padding: "16px" }}>
          <h3 style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.text }}>🔄 Media Diversification Framework</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 12, fontSize: 12 }}>
            <div style={{ background: C.card, borderRadius: 6, padding: "12px" }}>
              <div style={{ color: C.blue, fontWeight: 600 }}>Left-Leaning</div>
              <div style={{ color: C.muted }}>CNN, MSNBC, Vox</div>
            </div>
            <div style={{ background: C.card, borderRadius: 6, padding: "12px" }}>
              <div style={{ color: C.green, fontWeight: 600 }}>Center/Business</div>
              <div style={{ color: C.muted }}>Reuters, AP, CNBC, WSJ</div>
            </div>
            <div style={{ background: C.card, borderRadius: 6, padding: "12px" }}>
              <div style={{ color: C.red, fontWeight: 600 }}>Right-Leaning</div>
              <div style={{ color: C.muted }}>Fox Business, NY Post</div>
            </div>
          </div>
          <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>Goal: Detect narrative concentration in any single quadrant</p>
        </div>
      </div>

      {/* Narrative Consensus Score */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>📊 Narrative Consensus Score</h2>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 16 }}>
          {[
            { label: "Narrative Consensus", desc: "Degree of agreement across sources", icon: "🤝" },
            { label: "Narrative Dispersion", desc: "Degree of disagreement across sources", icon: "📊" },
            { label: "Narrative Intensity", desc: "Strength of overall sentiment", icon: "💪" },
          ].map((item) => (
            <div key={item.label} style={{ background: C.bg, borderRadius: 8, padding: "16px", textAlign: "center" }}>
              <div style={{ fontSize: 24 }}>{item.icon}</div>
              <div style={{ fontSize: 13, color: C.text, fontWeight: 600, marginTop: 4 }}>{item.label}</div>
              <div style={{ fontSize: 11, color: C.muted }}>{item.desc}</div>
            </div>
          ))}
        </div>
        <div style={{ background: C.accentBg, borderRadius: 8, padding: "12px", marginTop: 12 }}>
          <p style={{ fontSize: 11, color: C.muted, textAlign: "center", margin: 0 }}>
            When Consensus is high but Intensity decelerates with flat/falling prices → <strong style={{ color: C.accent }}>Narrative Exhaustion</strong>
          </p>
        </div>
      </div>

      {/* Sector Coverage */}
      <div style={{ background: C.card, borderRadius: 12, padding: "20px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: C.accent }}>📈 Sector-Level Coverage</h2>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {["Technology", "Financial Services", "Energy", "Industrials", "Healthcare", "Consumer", "Semiconductors"].map((sector) => (
            <span key={sector} style={{ background: C.bg, borderRadius: 20, padding: "4px 14px", fontSize: 12, color: C.text }}>
              {sector}
            </span>
          ))}
        </div>
        <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>Objective: Identify emerging narrative concentrations before they appear in broad market indices</p>
      </div>

      {/* Philosophy */}
      <div style={{ background: C.accentBg, borderRadius: 12, padding: "20px", border: `1px solid ${C.accent}` }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: C.accent }}>🧠 Information Philosophy</h2>
        <p style={{ fontSize: 13, fontStyle: "italic", color: C.muted, lineHeight: 1.6 }}>
          "No single source possesses complete information. Market narratives emerge from the interaction of thousands of independent information signals. 
          The objective is not to predict the future from a single article, but to measure how collective narratives evolve, strengthen, weaken, and diverge from underlying market behavior."
        </p>
        <p style={{ fontSize: 11, color: C.dim, marginTop: 12, textAlign: "right" }}>— SignalIQ Data Philosophy</p>
      </div>
    </div>
  );
}