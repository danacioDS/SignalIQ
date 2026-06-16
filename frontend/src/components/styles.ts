export const C = {
  // Fondo
  bg: "#0e1117",
  sidebar: "#131720",
  card: "#181f2e",
  cardBorder: "rgba(255,255,255,0.06)",
  
  // Texto
  text: "#e2e8f0",
  muted: "#6b7280",
  dim: "#374151",
  
  // Colores principales
  accent: "#6c63ff",
  accentBg: "rgba(108,99,255,0.15)",
  
  // Regímenes
  green: "#10b981",
  greenBg: "rgba(16,185,129,0.15)",
  red: "#ef4444",
  redBg: "rgba(239,68,68,0.15)",
  yellow: "#f59e0b",
  yellowBg: "rgba(245,158,11,0.15)",
  blue: "#3b82f6",
  blueBg: "rgba(59,130,246,0.15)",
  
  // Tipografía
  font: "'Inter', 'Segoe UI', sans-serif",
};

// ── Tipos de régimen ──────────────────────────────────────────────────────────
export const REGIMES = {
  OVERHEATING: { label: "Overheating", color: C.red, bg: C.redBg, icon: "🔴" },
  WATCHING: { label: "Watching", color: C.yellow, bg: C.yellowBg, icon: "🟡" },
  ALIGNED: { label: "Aligned", color: C.green, bg: C.greenBg, icon: "🟢" },
  UNDERVALUED: { label: "Undervalued", color: C.blue, bg: C.blueBg, icon: "🔵" },
};

export function getRegime(ndi: number) {
  if (ndi > 1.5) return REGIMES.OVERHEATING;
  if (ndi > 0.5) return REGIMES.WATCHING;
  if (ndi > -0.5) return REGIMES.ALIGNED;
  return REGIMES.UNDERVALUED;
}