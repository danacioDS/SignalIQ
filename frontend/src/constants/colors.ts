export const REGIME_COLORS = {
  extreme_overheating: '#ef4444',
  overheating: '#f97316',
  watching: '#eab308',
  equilibrium: '#22c55e',
  buy_opportunity: '#3b82f6',
  strong_undervalued: '#7C4DFF',
  capitulation: '#6b21a8',
} as const;

export const REGIME_LABELS = {
  extreme_overheating: 'Extreme Overheating',
  overheating: 'Overheating',
  watching: 'Watching',
  equilibrium: 'Equilibrium',
  buy_opportunity: 'Buy Opportunity',
  strong_undervalued: 'Strong Undervalued',
  capitulation: 'Capitulation',
} as const;

export const REGIME_ICONS = {
  extreme_overheating: '🔴',
  overheating: '🟠',
  watching: '🟡',
  equilibrium: '🟢',
  buy_opportunity: '🔵',
  strong_undervalued: '🟣',
  capitulation: '💎',
} as const;

export const REGIME_RANGES = {
  extreme_overheating: { min: 2.0, max: Infinity },
  overheating: { min: 1.5, max: 2.0 },
  watching: { min: 0.5, max: 1.5 },
  equilibrium: { min: -0.5, max: 0.5 },
  buy_opportunity: { min: -1.5, max: -0.5 },
  strong_undervalued: { min: -2.0, max: -1.5 },
  capitulation: { min: -Infinity, max: -2.0 },
} as const;

export type RegimeKey = keyof typeof REGIME_COLORS;

export const getRegimeKey = (ndi: number): RegimeKey => {
  for (const [key, range] of Object.entries(REGIME_RANGES)) {
    if (ndi > range.min && ndi <= range.max) {
      return key as RegimeKey;
    }
  }
  return 'equilibrium';
};

export const getRegimeColor = (ndi: number): string => {
  return REGIME_COLORS[getRegimeKey(ndi)];
};

export const getRegimeLabel = (ndi: number): string => {
  return REGIME_LABELS[getRegimeKey(ndi)];
};

export const getRegimeIcon = (ndi: number): string => {
  return REGIME_ICONS[getRegimeKey(ndi)];
};
