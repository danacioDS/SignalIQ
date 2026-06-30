/**
 * velocimeterUtils.ts
 * Utils para el velocímetro NDI
 * - Cálculo de ángulo de aguja
 * - Mapeo NDI → Régimen
 * - Colores, iconos, etiquetas
 */

// ── RANGO NDI ────────────────────────────────────────────────────────────────
export const NDI_RANGE = {
  min: -3.0,
  max: 3.0,
};

// ── REGÍMENES ─────────────────────────────────────────────────────────────────
export type RegimeKey =
  | 'EXTREME_OVERHEATING'
  | 'OVERHEATING'
  | 'WATCHING'
  | 'STABLE'
  | 'ALIGNED'
  | 'STRONG_UNDERVALUED'
  | 'EXTREME_UNDERVALUED';

export const REGIME_CONFIG: Record<RegimeKey, {
  label: string;
  icon: string;
  color: string;
  range: string;
}> = {
  EXTREME_OVERHEATING: {
    label: 'Extreme Overheating',
    icon: '🔴',
    color: '#ef4444',
    range: 'NDI > 2.0',
  },
  OVERHEATING: {
    label: 'Overheating',
    icon: '🟠',
    color: '#f97316',
    range: '1.5 < NDI ≤ 2.0',
  },
  WATCHING: {
    label: 'Watching',
    icon: '🟡',
    color: '#eab308',
    range: '0.5 < NDI ≤ 1.5',
  },
  STABLE: {
    label: 'Stable',
    icon: '🟢',
    color: '#22c55e',
    range: '-0.5 < NDI ≤ 0.5',
  },
  ALIGNED: {
    label: 'Aligned',
    icon: '🟢',
    color: '#22c55e',
    range: '-1.5 < NDI ≤ -0.5',
  },
  STRONG_UNDERVALUED: {
    label: 'Strong Undervalued',
    icon: '🔵',
    color: '#3b82f6',
    range: '-2.0 < NDI ≤ -1.5',
  },
  EXTREME_UNDERVALUED: {
    label: 'Extreme Undervalued',
    icon: '🔵',
    color: '#1d4ed8',
    range: 'NDI ≤ -2.0',
  },
};

// ── OBTENER RÉGIMEN DESDE NDI ──────────────────────────────────────────────
export const getRegimeFromNDI = (ndi: number): RegimeKey => {
  if (ndi > 2.0) return 'EXTREME_OVERHEATING';
  if (ndi > 1.5) return 'OVERHEATING';
  if (ndi > 0.5) return 'WATCHING';
  if (ndi > -0.5) return 'STABLE';
  if (ndi > -1.5) return 'ALIGNED';
  if (ndi > -2.0) return 'STRONG_UNDERVALUED';
  return 'EXTREME_UNDERVALUED';
};

// ── HELPERS ──────────────────────────────────────────────────────────────────
export const getRegimeLabel = (regime: RegimeKey): string => {
  return REGIME_CONFIG[regime].label;
};

export const getRegimeIcon = (regime: RegimeKey): string => {
  return REGIME_CONFIG[regime].icon;
};

export const getRegimeColor = (regime: RegimeKey): string => {
  return REGIME_CONFIG[regime].color;
};

// ── CÁLCULO DE ÁNGULO DE LA AGUJA ──────────────────────────────────────────
export const getNeedleAngle = (ndi: number): number => {
  const { min, max } = NDI_RANGE;
  const minAngle = -90;
  const maxAngle = 90;
  const clampedNDI = Math.max(min, Math.min(max, ndi));
  const percentage = (clampedNDI - min) / (max - min);
  return minAngle + percentage * (maxAngle - minAngle);
};

// ── COLOR SEGÚN NDI (DIRECTO) ──────────────────────────────────────────────
export const getColorFromNDI = (ndi: number): string => {
  const regime = getRegimeFromNDI(ndi);
  return getRegimeColor(regime);
};
