import { C } from "./styles";

export default function About() {
  return (
    <div style={{ padding: "24px 32px", maxWidth: 1000 }}>
      <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 20 }}>📖 About SignalIQ</h1>
      
      <div style={{ background: C.card, borderRadius: 12, padding: "24px", marginBottom: 24, borderLeft: `4px solid ${C.accent}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 12, color: C.accent }}>The Story Behind SignalIQ</h2>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: C.muted, marginBottom: 16 }}>
          SignalIQ was born from a simple but powerful question: <strong style={{ color: C.text }}>What happens when what the market says doesn't match what the market does?</strong>
        </p>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: C.muted, marginBottom: 16 }}>
          For years, investors have relied on two sources of information: news (narrative) and prices (reality). But the relationship between them is not always linear. Stories can get ahead of prices, and prices can move without stories to support them.
        </p>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: C.muted, marginBottom: 16 }}>
          SignalIQ was developed to systematically measure that distance between narrative and price, using the <strong style={{ color: C.text }}>Narrative Divergence Index (NDI)</strong>.
        </p>
        <p style={{ fontSize: 13, lineHeight: 1.6, color: C.muted }}>
          It is not a predictor. It is a measure of risk conditions. When the narrative gets too far ahead of price, SignalIQ reports it as an early warning signal.
        </p>
      </div>

      <div style={{ background: C.card, borderRadius: 12, padding: "24px", marginBottom: 24, border: `1px solid ${C.cardBorder}` }}>
        <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16, color: C.text }}>👨‍💻 Author</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <p style={{ fontSize: 16, fontWeight: 700, color: C.text, margin: 0 }}>Daniel Canedo</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "8px 24px" }}>
            <span style={{ fontSize: 13, color: C.muted }}>🤖 ML Engineer at <strong style={{ color: C.text }}>Anyone AI</strong></span>
            <span style={{ fontSize: 13, color: C.muted }}>🎓 MSc. Economics — <strong style={{ color: C.text }}>Yokohama National University</strong></span>
            <span style={{ fontSize: 13, color: C.muted }}>📊 Economist — <strong style={{ color: C.text }}>Universidad Católica Boliviana</strong></span>
          </div>
          <p style={{ fontSize: 13, color: C.muted, marginTop: 12, fontStyle: "italic" }}>
            "This software was designed and built by Daniel Canedo as part of the SignalIQ project."
          </p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div style={{ background: C.card, borderRadius: 8, padding: "16px", border: `1px solid ${C.cardBorder}` }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: C.accent }}>🎯 Why SignalIQ?</h3>
          <p style={{ fontSize: 12, color: C.muted, lineHeight: 1.5 }}>
            Markets don't move on good news. They move on news that exceeds expectations. SignalIQ measures when expectations are saturated.
          </p>
        </div>
        <div style={{ background: C.card, borderRadius: 8, padding: "16px", border: `1px solid ${C.cardBorder}` }}>
          <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: C.accent }}>🔬 Academic Foundation</h3>
          <p style={{ fontSize: 12, color: C.muted, lineHeight: 1.5 }}>
            Based on Keynes (Animal Spirits), Kahneman (Bounded Rationality), Dornbusch (Overshooting), and Fama (Market Efficiency).
          </p>
        </div>
      </div>
    </div>
  );
}