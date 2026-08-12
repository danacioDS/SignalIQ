import { C } from "./styles";

export default function EconomicFoundation() {
  return (
    <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📚 Economic Foundation</h1>
      <div style={{ display: "grid", gap: 20 }}>
        {/* Animal Spirits */}
        <div style={{ background: C.card, borderLeft: `4px solid ${C.accent}`, borderRadius: 8, padding: "20px" }}>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>Animal Spirits</h3>
          <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Keynes (1936); Akerlof & Shiller (2009)</p>
          <p style={{ fontSize: 13, lineHeight: 1.5 }}>Economic decisions are not purely rational. They are driven by confidence, fear, enthusiasm, and collective narratives. Financial news is the observable manifestation of these "animal spirits."</p>
        </div>

        {/* Bounded Rationality */}
        <div style={{ background: C.card, borderLeft: `4px solid ${C.blue}`, borderRadius: 8, padding: "20px" }}>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>Bounded Rationality</h3>
          <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Kahneman & Tversky (1979)</p>
          <p style={{ fontSize: 13, lineHeight: 1.5 }}>Investors do not process all available information. They use mental shortcuts (heuristics) that generate systematic biases: overconfidence, loss aversion, and overreaction to salient narratives.</p>
        </div>

        {/* Overshooting */}
        <div style={{ background: C.card, borderLeft: `4px solid ${C.green}`, borderRadius: 8, padding: "20px" }}>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>Overshooting</h3>
          <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Dornbusch (1976)</p>
          <p style={{ fontSize: 13, lineHeight: 1.5, fontStyle: "italic" }}>"Because financial markets adjust much faster than real economy prices and wages, exchange rates can initially react more than necessary to an economic shock, then partially reverse that movement as the economy converges to the new equilibrium."</p>
        </div>

        {/* Efficient Market Hypothesis */}
        <div style={{ background: C.card, borderLeft: `4px solid ${C.yellow}`, borderRadius: 8, padding: "20px" }}>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>Efficient Market Hypothesis</h3>
          <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Fama (1970)</p>
          <p style={{ fontSize: 13, lineHeight: 1.5, fontStyle: "italic" }}>"A market in which prices always fully reflect available information is called efficient."</p>
          <p style={{ fontSize: 12, color: C.muted, marginTop: 12 }}>"The primary role of the capital market is allocation of ownership of the economy's capital stock. In general terms, the ideal market is one in which prices provide accurate signals for resource allocation."</p>
          <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>— Fama, E. F. (1970). Efficient Capital Markets: A Review of Theory and Empirical Work. <em>Journal of Finance</em>, 25(2), 383–417.</p>
        </div>

        {/* SignalIQ Hypothesis */}
        <div style={{ background: C.accentBg, borderRadius: 8, padding: "24px", border: `1px solid ${C.accent}` }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12, color: C.accent }}>🎯 The SignalIQ Hypothesis</h3>
          <p style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>"When news sentiment remains strongly positive while price momentum weakens or stalls, market expectations may already be fully priced in. This sentiment-price divergence can signal an increased probability of consolidation or downside volatility over subsequent trading periods."</p>
          <div style={{ background: C.bg, borderRadius: 8, padding: "16px", marginTop: 8 }}>
            <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.muted }}>📊 Core Principle</p>
            <p style={{ fontSize: 13, fontStyle: "italic", lineHeight: 1.5 }}>"Markets don't move on good news. They move on news that exceeds expectations. If sentiment stays highly positive but price stops responding, expectations may already be saturated. SignalIQ identifies these sentiment-price divergences as potential early warning signals."</p>
          </div>
        </div>

        {/* 📊 Confidence: Signal Quality */}
        <div style={{ background: C.card, borderLeft: `4px solid ${C.purple}`, borderRadius: 8, padding: "20px" }}>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>📊 Confidence: Signal Quality</h3>
          <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>SignalIQ Internal Metric</p>
          <p style={{ fontSize: 13, lineHeight: 1.5, marginBottom: 12 }}>
            <strong>Confidence</strong> is a quality metric that measures how reliable the NDI signal is for a given ticker at a given time.
          </p>

          <h4 style={{ fontSize: 14, fontWeight: 600, marginTop: 12, marginBottom: 8, color: C.text }}>How is it calculated?</h4>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <th style={{ textAlign: "left", padding: "6px 8px", color: C.muted }}>Factor</th>
                  <th style={{ textAlign: "center", padding: "6px 8px", color: C.muted }}>Weight</th>
                  <th style={{ textAlign: "left", padding: "6px 8px", color: C.muted }}>Why</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px" }}>Long history (≥30 days)</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.green }}>+20%</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>More data = better estimation</td>
                </tr>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px" }}>Significant divergence (NDI &gt; 0.5)</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.green }}>+15%</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>Clearer, more differentiated signal</td>
                </tr>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px" }}>Strong divergence (NDI &gt; 1.0)</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.green }}>+10%</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>Very clear signal</td>
                </tr>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px" }}>Real news (&gt;0)</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.green }}>+10%</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>Real data, not simulated</td>
                </tr>
                <tr>
                  <td style={{ padding: "6px 8px" }}>Base</td>
                  <td style={{ textAlign: "center", padding: "6px 8px" }}>50%</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>Neutral default value</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h4 style={{ fontSize: 14, fontWeight: 600, marginTop: 16, marginBottom: 8, color: C.text }}>Confidence Scale</h4>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <th style={{ textAlign: "left", padding: "6px 8px", color: C.muted }}>Range</th>
                  <th style={{ textAlign: "left", padding: "6px 8px", color: C.muted }}>Meaning</th>
                  <th style={{ textAlign: "left", padding: "6px 8px", color: C.muted }}>Implication</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px", color: C.green, fontWeight: 600 }}>90-95%</td>
                  <td style={{ padding: "6px 8px" }}>Very High</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>Robust data, clear signal, sufficient history</td>
                </tr>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px", color: C.green }}>70-89%</td>
                  <td style={{ padding: "6px 8px" }}>High</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>Reliable signal, good history</td>
                </tr>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px", color: C.yellow }}>50-69%</td>
                  <td style={{ padding: "6px 8px" }}>Moderate</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>Acceptable signal, consider context</td>
                </tr>
                <tr>
                  <td style={{ padding: "6px 8px", color: C.red }}>&lt; 50%</td>
                  <td style={{ padding: "6px 8px" }}>Low</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>Limited data, weak signal, use with caution</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h4 style={{ fontSize: 14, fontWeight: 600, marginTop: 16, marginBottom: 8, color: C.text }}>Example Interpretation</h4>
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <th style={{ textAlign: "left", padding: "6px 8px", color: C.muted }}>Ticker</th>
                  <th style={{ textAlign: "center", padding: "6px 8px", color: C.muted }}>NDI</th>
                  <th style={{ textAlign: "center", padding: "6px 8px", color: C.muted }}>Confidence</th>
                  <th style={{ textAlign: "left", padding: "6px 8px", color: C.muted }}>Interpretation</th>
                </tr>
              </thead>
              <tbody>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px", fontWeight: 600 }}>MSFT</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.blue }}>-0.770</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.green, fontWeight: 600 }}>88%</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>✅ Long history + real news + clear signal → Very reliable</td>
                </tr>
                <tr style={{ borderBottom: `1px solid ${C.cardBorder}` }}>
                  <td style={{ padding: "6px 8px", fontWeight: 600 }}>NVDA</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.green }}>0.280</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.green, fontWeight: 600 }}>80%</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>✅ Long history + real news → Reliable</td>
                </tr>
                <tr>
                  <td style={{ padding: "6px 8px", fontWeight: 600 }}>AAPL</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.yellow }}>0.503</td>
                  <td style={{ textAlign: "center", padding: "6px 8px", color: C.green, fontWeight: 600 }}>75%</td>
                  <td style={{ padding: "6px 8px", color: C.muted }}>✅ Long history + real news → Reliable</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* Academic References */}
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
}