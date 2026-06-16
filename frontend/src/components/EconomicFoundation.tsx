import { C } from "./styles";

export default function EconomicFoundation() {
  return (
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
          <p style={{ fontSize: 13, lineHeight: 1.5, fontStyle: "italic" }}>"Because financial markets adjust much faster than real economy prices and wages, exchange rates can initially react more than necessary to an economic shock, then partially reverse that movement as the economy converges to the new equilibrium."</p>
        </div>
        <div style={{ background: C.card, borderLeft: `4px solid ${C.yellow}`, borderRadius: 8, padding: "20px" }}>
          <h3 style={{ fontSize: 18, fontWeight: 600 }}>Efficient Market Hypothesis</h3>
          <p style={{ fontSize: 12, color: C.muted, marginBottom: 10 }}>Fama (1970)</p>
          <p style={{ fontSize: 13, lineHeight: 1.5, fontStyle: "italic" }}>"A market in which prices always fully reflect available information is called efficient."</p>
          <p style={{ fontSize: 12, color: C.muted, marginTop: 12 }}>"The primary role of the capital market is allocation of ownership of the economy's capital stock. In general terms, the ideal market is one in which prices provide accurate signals for resource allocation."</p>
          <p style={{ fontSize: 10, color: C.dim, marginTop: 8 }}>— Fama, E. F. (1970). Efficient Capital Markets: A Review of Theory and Empirical Work. <em>Journal of Finance</em>, 25(2), 383–417.</p>
        </div>
        <div style={{ background: C.accentBg, borderRadius: 8, padding: "24px", border: `1px solid ${C.accent}` }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, marginBottom: 12, color: C.accent }}>🎯 The SignalIQ Hypothesis</h3>
          <p style={{ fontSize: 14, lineHeight: 1.6, marginBottom: 20 }}>"When news sentiment remains strongly positive while price momentum weakens or stalls, market expectations may already be fully priced in. This sentiment-price divergence can signal an increased probability of consolidation or downside volatility over subsequent trading periods."</p>
          <div style={{ background: C.bg, borderRadius: 8, padding: "16px", marginTop: 8 }}>
            <p style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: C.muted }}>📊 Core Principle</p>
            <p style={{ fontSize: 13, fontStyle: "italic", lineHeight: 1.5 }}>"Markets don't move on good news. They move on news that exceeds expectations. If sentiment stays highly positive but price stops responding, expectations may already be saturated. SignalIQ identifies these sentiment-price divergences as potential early warning signals."</p>
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
}